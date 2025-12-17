"""Mail extension for InKCre - provides IMAP email source."""

import sqlmodel
from fastapi import APIRouter
from app.business.extension import ExtensionBase


class MailExtensionConfig(sqlmodel.SQLModel):
    """Configuration for mail extension."""

    ...


class Extension(
    ExtensionBase[MailExtensionConfig],
    ext_id="mail",
    config_cls=MailExtensionConfig,
):
    """Mail extension - provides IMAP source for collecting emails."""

    @classmethod
    def _init_resolvers(cls):
        """Initialize email resolver."""
        from .resolver import EmailResolver  # noqa: F401
        from .resolver import NewsletterResolver  # noqa: F401

    @classmethod
    def _init_sources(cls):
        """Initialize IMAP source."""
        from .imap import Source as IMAPSource  # noqa: F401
        from .newsletter import Source as NewsletterSource  # noqa: F401

    @classmethod
    def _register_apis(cls, router: APIRouter):
        """Register API endpoints for mail extension."""
        from app.business.source import SourceManager

        router.post("/imap")(
            lambda nickname: SourceManager.create(
                f"extensions.{cls.__extid__}.imap.Source", nickname
            )
        )

        router.post("/newsletter")(
            lambda nickname: SourceManager.create(
                f"extensions.{cls.__extid__}.newsletter.Source", nickname
            )
        )
