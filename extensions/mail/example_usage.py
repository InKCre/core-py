"""Example usage of the mail extension with IMAP source.

This example demonstrates how to:
1. Install and configure the mail extension
2. Create an IMAP source
3. Collect emails
"""

from app.business.source import SourceManager
from app.schemas.extension import ExtensionModel
from app.schemas.source import SourceModel, CollectAt
from app.engine import SessionLocal


async def example_setup_and_collect():
    """Example of setting up and using the mail extension."""
    
    # Step 1: Install the mail extension in the database
    # (This would typically be done via migration or admin panel)
    with SessionLocal() as db:
        extension = ExtensionModel(
            id="mail",
            version="0.1.0",
            disabled=False,
            config={
                "imap_server": "imap.gmail.com",
                "imap_port": 993,
                "use_ssl": True,
                "username": "your-email@gmail.com",
                "password": "your-app-password",  # Use app-specific password for Gmail
            },
            state={"last_uid": None}
        )
        db.add(extension)
        db.commit()
    
    # Step 2: Create an IMAP source
    # Via API: POST /mail/imap with nickname parameter
    # Or programmatically:
    source = SourceManager.create(
        type_="extensions.mail.imap_source",
        nickname="My Gmail Inbox"
    )
    
    # Step 3: Configure collection schedule (optional)
    # Collect emails every day at 9 AM
    with SessionLocal() as db:
        source_model = db.get(SourceModel, source.id)
        if source_model:
            source_model.collect_at = CollectAt(hour=9, minute=0)
            db.commit()
    
    # Step 4: Run a manual collection
    collected_blocks = await SourceManager.run_a_collect(
        source_id=source.id,
        full=False  # Only collect new emails
    )
    
    print(f"Collected {len(collected_blocks)} emails")
    
    # For full collection (all emails):
    # collected_blocks = await SourceManager.run_a_collect(
    #     source_id=source.id,
    #     full=True
    # )


if __name__ == "__main__":
    # Note: This example requires a configured database and extension system
    # In practice, you'd use the API endpoints or admin interface
    print("Mail Extension Usage Example")
    print("=" * 50)
    print()
    print("To use the mail extension:")
    print("1. Install the extension in your InKCre instance")
    print("2. Configure IMAP settings (server, port, credentials)")
    print("3. Create an IMAP source via POST /mail/imap")
    print("4. Trigger collection via GET /source/{source_id}/collect")
    print()
    print("For Gmail users:")
    print("- Use app-specific password instead of account password")
    print("- Enable IMAP in Gmail settings")
    print("- Server: imap.gmail.com, Port: 993, SSL: true")
