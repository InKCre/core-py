"""Newsletter Source for collecting newsletters from IMAP."""

import asyncio
import email
import imaplib

import sqlmodel
from app.business.source import SourceBase
from app.business.info_base.root import RootManager
from app.engine import SessionLocal
from app.schemas.info_base.block import BlockID, BlockModel
from app.schemas.info_base.main import StarGraphForm
from app.schemas.source import SourceCollectJobModel
from app.scheduler import scheduler
from libs.obsrv.main import get_logger

from .imap import Source as IMAPSource
from .schema import Newsletter

LOGGER = get_logger().getChild(__name__)


class NewsletterSourceConfig(sqlmodel.SQLModel):
  """Configuration of Newsletter Source."""

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
  newsletter_name: str = ""
  """Name of the newsletter source"""
  sender_email: str = ""
  """Email address of the newsletter sender"""
  mailbox: str = "INBOX"
  """Mailbox to collect from (default: INBOX)"""


class Source(SourceBase[NewsletterSourceConfig], config_cls=NewsletterSourceConfig):
  """Newsletter Source - collects newsletters from IMAP server by filtering sender."""

  async def collect(self, job: SourceCollectJobModel) -> None:
    """Collect newsletters from IMAP server."""
    logger = LOGGER.getChild(f"collect.{job.id}")
    config = self.get_config()
    job_config = job.config or {}
    full = job_config.get("full", False)

    logger.info(
      "Starting newsletter collection",
      extra={
        "job_id": job.id,
        "source": job.source,
        "full": full,
        "newsletter_name": config.newsletter_name,
        "sender_email": config.sender_email,
        "mailbox": config.mailbox,
      },
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

      # Select mailbox
      try:
        mail.select(config.mailbox)
        logger.info("Selected mailbox", extra={"mailbox": config.mailbox})
      except Exception as e:
        logger.error(
          "Failed to select mailbox",
          extra={"mailbox": config.mailbox, "error": str(e)},
          exc_info=True,
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
          last_seen_uid = state.get("last_seen_uid")
          if last_seen_uid:
            _, message_numbers = mail.search(None, f"UID {last_seen_uid + 1}:*")
            logger.info(
              "Searching for new emails since UID",
              extra={"last_seen_uid": last_seen_uid},
            )
          else:
            # No last UID, get recent emails
            _, message_numbers = mail.search(None, "RECENT")
            logger.info("Searching for recent emails (no last UID)")
      except Exception as e:
        logger.error("Failed to search emails", extra={"error": str(e)}, exc_info=True)
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
        logger.debug("Processing email", extra={"num": int(num)})
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
          logger.debug("Skipping email, no data", extra={"num": int(num)})
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

        # Extract sender email
        from_addr = IMAPSource._parse_email_address(msg.get("From"))

        # Filter by sender email
        if not from_addr or from_addr.email.lower() != config.sender_email.lower():
          logger.debug(
            "Skipping email, sender does not match",
            extra={
              "num": int(num),
              "from": from_addr.email if from_addr else None,
              "expected": config.sender_email,
            },
          )
          continue

        # Extract email data
        subject = IMAPSource._decode_header(msg.get("Subject", ""))

        # Get email body - prefer plain text, fallback to HTML
        body_text, body_html = IMAPSource._get_email_body(msg)
        body = body_text if body_text else body_html if body_html else ""

        if not body:
          logger.debug(
            "Skipping email, no body content",
            extra={"num": int(num), "subject": subject},
          )
          continue

        # Create Newsletter object
        newsletter_obj = Newsletter(
          subject=subject,
          body=body,
        )

        # Update last_seen_uid incrementally
        if uid:
          state = self.get_state()
          current_last_uid = state.get("last_seen_uid", 0)
          if uid > current_last_uid:
            state["last_seen_uid"] = uid
            self.set_state(state)
            logger.debug("Updated last_seen_uid", extra={"new_uid": uid})

        # Collect as StarGraphForm
        collected.append(
          StarGraphForm(
            block=BlockModel(
              resolver="extensions.mail.resolver.NewsletterResolver",
              content=newsletter_obj.model_dump_json(),
            ),
            out_relations=(),
          )
        )
        logger.debug(
          "Collected newsletter",
          extra={"uid": uid, "subject": subject},
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

    logger.info("Saving collected newsletters to database", extra={"count": len(collected)})
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
        "Newsletter collection completed",
        extra={"job_id": job.id, "newsletters_collected": len(collected)},
      )
    except Exception as e:
      logger.error(
        "Failed to save newsletters to database",
        extra={"job_id": job.id, "error": str(e)},
        exc_info=True,
      )

  async def _organize(self, block_id: BlockID) -> None:
    """Organize collected newsletter block.

    Currently no additional organization needed for newsletters.
    """
    pass
