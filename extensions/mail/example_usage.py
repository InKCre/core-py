"""Example usage of the mail extension with IMAP source.

This example demonstrates how to:
1. Install and configure the mail extension
2. Create an IMAP source
3. Collect emails

Note: This is a conceptual example. In practice, use environment variables
for credentials and configure via the API or admin interface.
"""

from app.business.source import SourceManager
from app.schemas.extension import ExtensionModel
from app.schemas.source import SourceModel, CollectAt
from app.engine import SessionLocal


def setup_mail_extension():
    """Example: Install the mail extension in the database.
    
    In production, this would be done via migration or admin panel.
    """
    with SessionLocal() as db:
        extension = ExtensionModel(
            id="mail",
            version="0.1.0",
            disabled=False,
            config={
                "imap_server": "imap.example.com",  # Replace with actual server
                "imap_port": 993,
                "use_ssl": True,
                "username": "YOUR_EMAIL@example.com",  # Use environment variable
                "password": "YOUR_APP_PASSWORD",  # Use environment variable - NEVER hardcode!
            },
            state={"last_uid": None}
        )
        db.add(extension)
        db.commit()


def create_imap_source():
    """Example: Create an IMAP source programmatically.
    
    Alternatively, use the API endpoint: POST /mail/imap
    """
    source = SourceManager.create(
        type_="extensions.mail.imap_source",
        nickname="My Inbox"
    )
    return source


def configure_collection_schedule(source_id):
    """Example: Configure automatic collection schedule.
    
    This sets up daily collection at 9 AM.
    """
    with SessionLocal() as db:
        source_model = db.get(SourceModel, source_id)
        if source_model:
            source_model.collect_at = CollectAt(hour=9, minute=0)
            db.commit()


# Recommended usage via API:
USAGE_GUIDE = """
Mail Extension - Recommended Usage via API
===========================================

1. Install extension (via database migration or admin panel):
   INSERT INTO extensions (id, version, config, state)
   VALUES ('mail', '0.1.0', {...}, {...});

2. Configure IMAP settings in the extension config:
   {
       "imap_server": "imap.gmail.com",
       "imap_port": 993,
       "use_ssl": true,
       "username": "${IMAP_USERNAME}",  # Use environment variables!
       "password": "${IMAP_PASSWORD}"   # Use app-specific password for Gmail
   }

3. Create an IMAP source:
   POST /mail/imap?nickname=My%20Gmail%20Inbox

4. Trigger collection:
   GET /source/{source_id}/collect?full=false

5. Schedule automatic collection:
   Update source.collect_at in database with desired schedule

Gmail-specific notes:
- Enable IMAP in Gmail settings
- Use app-specific password (not account password)
- Server: imap.gmail.com, Port: 993, SSL: true
"""

if __name__ == "__main__":
    print(USAGE_GUIDE)
