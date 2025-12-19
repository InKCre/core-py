"""IMAP Source for collecting emails."""

import asyncio
import email
import imaplib
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional as Opt

import sqlmodel
from app.business.source import SourceBase
from app.engine import SessionLocal
from app.business.root import RootManager
from app.schemas.root import StarGraphForm
from app.schemas.block import BlockModel
from app.schemas.block import BlockID
from app.schemas.source import SourceCollectJobModel
from app.scheduler import scheduler
from libs.obsrv.main import get_logger
from .schema import Email, EmailAddress

LOGGER = get_logger().getChild(__name__)


class SourceConfig(sqlmodel.SQLModel):
    """Configuration of IMAP Source."""

    imap_server: str = ""
    """IMAP server address (e.g., imap.gmail.com)"""
    imap_port: int = 993
    """IMAP port (default: 993 for SSL)"""
    use_ssl: bool = True
    """Whether to use SSL/TLS connection"""
    username: str = ""
    """Email account username"""
    password: str = ""
    """Email account password or app-specific password"""


class Source(SourceBase[SourceConfig], config_cls=SourceConfig):
    """IMAP Source - collects emails from IMAP server."""

    @classmethod
    def _decode_header(cls, header_value: Opt[str]) -> str:
        """Decode email header value."""
        if not header_value:
            return ""

        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or "utf-8", errors="ignore"))
                except (LookupError, AttributeError):
                    decoded_parts.append(part.decode("utf-8", errors="ignore"))
            else:
                decoded_parts.append(str(part))
        return "".join(decoded_parts)

    @classmethod
    def _parse_email_address(cls, addr_str: Opt[str]) -> Opt[EmailAddress]:
        """Parse email address from string."""
        if not addr_str:
            return None
        name, email_addr = parseaddr(addr_str)
        if not email_addr:
            return None
        return EmailAddress(
            email=email_addr, name=cls._decode_header(name) if name else None
        )

    @classmethod
    def _parse_email_addresses(cls, addr_str: Opt[str]) -> list[EmailAddress]:
        """Parse multiple email addresses from string."""
        if not addr_str:
            return []
        addresses = []
        # Simple split on comma - may need more sophisticated parsing
        for addr in addr_str.split(","):
            parsed = cls._parse_email_address(addr.strip())
            if parsed:
                addresses.append(parsed)
        return addresses

    @classmethod
    def _get_email_body(cls, msg: Message) -> tuple[Opt[str], Opt[str]]:
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
                            body_text = payload.decode(errors="ignore")
                    except Exception:
                        pass
                elif content_type == "text/html" and not body_html:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_html = payload.decode(errors="ignore")
                    except Exception:
                        pass
        else:
            # Not multipart - simple email
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    decoded = payload.decode(errors="ignore")
                    if content_type == "text/plain":
                        body_text = decoded
                    elif content_type == "text/html":
                        body_html = decoded
            except Exception:
                pass

        return body_text, body_html

    @classmethod
    def _has_attachments(cls, msg: Message) -> bool:
        """Check if email has attachments."""
        if not msg.is_multipart():
            return False

        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                return True
        return False

    async def collect(self, job: SourceCollectJobModel) -> None:
        """Collect emails from IMAP server.

        By default, collects new unseen emails since last collection by UID.
        If last UID is not available, collects recent unseen emails.
        (recent refers to since last 7 days)
        """
        logger = LOGGER.getChild(f"collect.{job.id}")
        config = self.get_config()
        job_config = job.config or {}
        full = job_config.get("full", False)

        logger.info(
            "Starting email collection",
            extra={"job_id": job.id, "source": job.source, "full": full},
        )

        # Connect to IMAP server
        try:
            if config.use_ssl:
                mail = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            else:
                mail = imaplib.IMAP4(config.imap_server, config.imap_port)
            logger.info(
                "Connected to IMAP server",
                extra={
                    "server": config.imap_server,
                    "port": config.imap_port,
                    "ssl": config.use_ssl,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to connect to IMAP server",
                extra={
                    "server": config.imap_server,
                    "port": config.imap_port,
                    "error": str(e),
                },
                exc_info=True,
            )
            return

        collected = []
        try:
            # Login
            try:
                mail.login(config.username, config.password)
                logger.info("Logged in to IMAP server")
            except Exception as e:
                logger.error(
                    "Failed to login to IMAP server",
                    extra={"username": config.username, "error": str(e)},
                    exc_info=True,
                )
                return

            # Select inbox
            try:
                mail.select("INBOX")
                logger.info("Selected mailbox INBOX")
            except Exception as e:
                logger.error(
                    "Failed to select mailbox INBOX", extra={"error": str(e)}, exc_info=True
                )
                return

            # Search for emails
            try:
                if full:
                    # Get all emails
                    _, message_numbers = mail.search(None, "ALL")
                    logger.info("Searching for all emails")
                else:
                    # Get only new emails since last UID
                    state = self.get_state()
                    last_uid = state.get("last_uid")
                    if last_uid:
                        _, message_numbers = mail.search(None, f"UID {last_uid + 1}:*")
                        logger.info(
                            "Searching for new emails since UID",
                            extra={"last_uid": last_uid},
                        )
                    else:
                        # No last UID, get recent emails
                        _, message_numbers = mail.search(
                            None,
                            "UNSEEN SINCE "
                            + (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y"),
                        )
                        logger.info("Searching for recent emails (no last UID)")
            except Exception as e:
                logger.error(
                    "Failed to search emails", extra={"error": str(e)}, exc_info=True
                )
                return

            if not message_numbers or not message_numbers[0]:
                logger.info("No emails found to process")
                return

            msg_nums = message_numbers[0].split()
            logger.info("Found emails to process", extra={"count": len(msg_nums)})

            # Process emails in reverse order for full collection
            if full:
                msg_nums = reversed(msg_nums)

            for num in msg_nums:
                logger.info("Processing email", extra={"num": int(num)})
                # Fetch email
                try:
                    _, msg_data = mail.fetch(num, "(RFC822 UID)")
                except Exception as e:
                    logger.warning(
                        "Failed to fetch email",
                        extra={"num": int(num), "error": str(e)},
                        exc_info=True,
                    )
                    continue

                if not msg_data or not msg_data[0]:
                    logger.warning("Skipping email, no data", extra={"num": int(num)})
                    continue

                # Parse UID
                uid_match = (
                    msg_data[0][0] if isinstance(msg_data[0], tuple) else msg_data[0]
                )
                uid = None
                if isinstance(uid_match, bytes):
                    uid_str = uid_match.decode()
                    if "UID" in uid_str:
                        uid = int(uid_str.split("UID")[1].split(")")[0].strip())

                # Parse email message
                email_body = (
                    msg_data[0][1] if isinstance(msg_data[0], tuple) else msg_data[0]
                )
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
                except Exception as e:
                    logger.warning(
                        "Failed to parse email date, using current time",
                        extra={"num": int(num), "date_str": date_str, "error": str(e)},
                    )
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
                        has_attachments=has_attachments,
                    )

                    # Update last UID
                    state = self.get_state()
                    if uid and (
                        not state.get("last_uid") or uid > state.get("last_uid", 0)
                    ):
                        state["last_uid"] = uid
                        self.set_state(state)
                        logger.debug("Updated last UID", extra={"new_uid": uid})

                    # Collect as StarGraphForm
                    collected.append(
                        StarGraphForm(
                            block=BlockModel(
                                resolver="extensions.mail.resolver.EmailResolver",
                                content=email_obj.model_dump_json(),
                            ),
                            out_relations=(),
                        )
                    )
                    logger.info(
                        "Collected email", extra={"uid": email_obj.uid, "subject": subject}
                    )
                else:
                    logger.warning(
                        "Skipping email, missing from or to addresses",
                        extra={"num": int(num), "subject": subject},
                    )

                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.1)

        finally:
            # Logout and close connection
            try:
                mail.logout()
                logger.info("Logged out from IMAP server")
            except Exception as e:
                logger.warning("Failed to logout from IMAP server", extra={"error": str(e)})

        logger.info("Saving collected emails to database", extra={"count": len(collected)})
        try:
            with SessionLocal() as db:
                for graph in reversed(collected) if full else collected:
                    await RootManager.add_star_graph_to_session(graph, db)
                    # Schedule organize
                    scheduler.add_job(
                        func=self._organize,
                        kwargs={"block_id": graph.block.id},
                        misfire_grace_time=None,
                    )
                db.commit()
            logger.info(
                "Email collection completed",
                extra={"job_id": job.id, "emails_collected": len(collected)},
            )
        except Exception as e:
            logger.error(
                "Failed to save emails to database",
                extra={"job_id": job.id, "error": str(e)},
                exc_info=True,
            )

    async def _organize(self, block_id: BlockID) -> None:
        """Organize collected email block.

        Currently no additional organization needed for emails.
        """
        pass
