"""IMAP Source for collecting emails."""

import asyncio
import email
import imaplib
import typing
from datetime import datetime
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional as Opt
from app.business.source import SourceBase
from app.schemas.root import StarGraphForm
from app.schemas.block import BlockModel
from app.schemas.block import BlockID
from extensions.mail import Extension
from .schema import Email, EmailAddress


class Source(SourceBase):
    """IMAP Source - collects emails from IMAP server."""

    def _decode_header(self, header_value: Opt[str]) -> str:
        """Decode email header value."""
        if not header_value:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
                except (LookupError, AttributeError):
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))
        return "".join(decoded_parts)

    def _parse_email_address(self, addr_str: Opt[str]) -> Opt[EmailAddress]:
        """Parse email address from string."""
        if not addr_str:
            return None
        name, email_addr = parseaddr(addr_str)
        if not email_addr:
            return None
        return EmailAddress(
            email=email_addr,
            name=self._decode_header(name) if name else None
        )

    def _parse_email_addresses(self, addr_str: Opt[str]) -> list[EmailAddress]:
        """Parse multiple email addresses from string."""
        if not addr_str:
            return []
        addresses = []
        # Simple split on comma - may need more sophisticated parsing
        for addr in addr_str.split(','):
            parsed = self._parse_email_address(addr.strip())
            if parsed:
                addresses.append(parsed)
        return addresses

    def _get_email_body(self, msg: email.message.Message) -> tuple[Opt[str], Opt[str]]:
        """Extract plain text and HTML body from email message."""
        body_text = None
        body_html = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain" and not body_text:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text = payload.decode(errors='ignore')
                    except Exception:
                        pass
                elif content_type == "text/html" and not body_html:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_html = payload.decode(errors='ignore')
                    except Exception:
                        pass
        else:
            # Not multipart - simple email
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    decoded = payload.decode(errors='ignore')
                    if content_type == "text/plain":
                        body_text = decoded
                    elif content_type == "text/html":
                        body_html = decoded
            except Exception:
                pass

        return body_text, body_html

    def _has_attachments(self, msg: email.message.Message) -> bool:
        """Check if email has attachments."""
        if not msg.is_multipart():
            return False
        
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                return True
        return False

    async def _collect(  # type: ignore[override]
        self, full: bool = False
    ) -> typing.AsyncGenerator[StarGraphForm, None]:
        """Collect emails from IMAP server.
        
        :param full: If True, collect all emails, otherwise only new ones.
        """
        config = Extension.config
        
        # Connect to IMAP server
        if config.use_ssl:
            mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
        else:
            mail = imaplib.IMAP4(config.imap_server, config.imap_port)
        
        try:
            # Login
            mail.login(config.username, config.password)
            
            # Select inbox
            mail.select("INBOX")
            
            # Search for emails
            if full:
                # Get all emails
                _, message_numbers = mail.search(None, "ALL")
            else:
                # Get only new emails since last UID
                last_uid = Extension.state.last_uid
                if last_uid:
                    _, message_numbers = mail.search(None, f"UID {last_uid + 1}:*")
                else:
                    # No last UID, get recent emails
                    _, message_numbers = mail.search(None, "RECENT")
            
            if not message_numbers or not message_numbers[0]:
                return
            
            msg_nums = message_numbers[0].split()
            
            # Process emails in reverse order for full collection
            if full:
                msg_nums = reversed(msg_nums)
            
            for num in msg_nums:
                # Fetch email
                _, msg_data = mail.fetch(num, "(RFC822 UID)")
                
                if not msg_data or not msg_data[0]:
                    continue
                
                # Parse UID
                uid_match = msg_data[0][0] if isinstance(msg_data[0], tuple) else msg_data[0]
                uid = None
                if isinstance(uid_match, bytes):
                    uid_str = uid_match.decode()
                    if "UID" in uid_str:
                        uid = int(uid_str.split("UID")[1].split(")")[0].strip())
                
                # Parse email message
                email_body = msg_data[0][1] if isinstance(msg_data[0], tuple) else msg_data[0]
                msg = email.message_from_bytes(email_body)
                
                # Extract email data
                subject = self._decode_header(msg.get("Subject", ""))
                from_addr = self._parse_email_address(msg.get("From"))
                to_addrs = self._parse_email_addresses(msg.get("To"))
                cc_addrs = self._parse_email_addresses(msg.get("Cc"))
                message_id = msg.get("Message-ID", "")
                
                # Parse date
                date_str = msg.get("Date")
                try:
                    date = parsedate_to_datetime(date_str) if date_str else datetime.now()
                except Exception:
                    date = datetime.now()
                
                # Get email body
                body_text, body_html = self._get_email_body(msg)
                has_attachments = self._has_attachments(msg)
                
                # Create Email object
                if from_addr and to_addrs:
                    email_obj = Email(
                        uid=uid or int(num),
                        message_id=message_id,
                        subject=subject,
                        from_=from_addr,
                        to=to_addrs,
                        cc=cc_addrs,
                        date=date,
                        body_text=body_text,
                        body_html=body_html,
                        has_attachments=has_attachments
                    )
                    
                    # Update last UID
                    if uid and (not Extension.state.last_uid or uid > Extension.state.last_uid):
                        Extension.state.last_uid = uid
                    
                    # Yield as StarGraphForm
                    yield StarGraphForm(
                        block=BlockModel(
                            resolver="extensions.mail.resolver.EmailResolver",
                            content=email_obj.model_dump_json(),
                        ),
                        out_relations=()
                    )
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.1)
        
        finally:
            # Logout and close connection
            try:
                mail.logout()
            except Exception:
                pass

    async def _organize(self, block_id: BlockID) -> None:
        """Organize collected email block.
        
        Currently no additional organization needed for emails.
        """
        pass
