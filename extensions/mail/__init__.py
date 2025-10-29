"""Mail extension for InKCre - provides IMAP email source."""

import sqlmodel
from typing import Optional as Opt
from fastapi import APIRouter
from app.business.extension import ExtensionBase


class MailExtensionConfig(sqlmodel.SQLModel):
    """Configuration for mail extension."""
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


class MailExtensionState(sqlmodel.SQLModel):
    """State for mail extension."""
    last_uid: Opt[int] = None
    """Last processed email UID"""


class Extension(
    ExtensionBase[MailExtensionConfig, MailExtensionState],
    ext_id="mail",
    config_cls=MailExtensionConfig,
    state_cls=MailExtensionState,
):
    """Mail extension - provides IMAP source for collecting emails."""

    @classmethod
    def _init_resolvers(cls):
        """Initialize email resolver."""
        from .resolver import EmailResolver  # noqa: F401

    @classmethod
    def _init_sources(cls):
        """Initialize IMAP source."""
        from .imap_source import Source as IMAPSource  # noqa: F401

    @classmethod
    def _register_apis(cls, router: APIRouter):
        """Register API endpoints for mail extension."""
        from app.business.source import SourceManager

        router.post("/imap")(
            lambda nickname: SourceManager.create(
                f"extensions.{cls.__extid__}.imap_source", nickname
            )
        )
