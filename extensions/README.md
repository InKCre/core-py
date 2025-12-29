# README of InKCre extensions

- Built-in and third-party extensions placed under `extensions/`.
- Folder name is the extension id.
- Extensions are disabled by default.

## Development

- Every extension has a `pyproject.toml` storing the extension metadata:

```toml
[project]
version = "0.1.0"  # as extension version

[tool.inkcre-ext]
id = "mail"  # optional since folder name is already the extension id
nickname = "Mail" 
```

## Writing Extension Components

### Source

Sources collect data as graphs and insert into the info-base.

Graphs consist of blocks and relations. To avoid complex database interaction, use `StarGraphForm` to automatically resolve references and insert all at once.

#### Guidelines for Writing a Source

1. **Inherit from `SourceBase` with a config class**:
   ```python
   from app.business.source import SourceBase
   import sqlmodel
   
   class SourceConfig(sqlmodel.SQLModel):
       """Configuration for this source."""
       api_key: str = ""
       server_url: str = ""
       # Add other configuration fields
   
   class Source(SourceBase[SourceConfig], config_cls=SourceConfig):
       """Your source description."""
       pass
   ```

2. **Implement the `collect` method**:
   - This is the main method that collects data from the external source
   - Use `self.get_config()` to access source configuration
   - Use `self.get_state()` and `self.set_state()` to manage collection state
   - Create `StarGraphForm` objects for collected data
   - Save to database using `RootManager.add_star_graph_to_session()`
   
   Example:
   ```python
   async def collect(self, job: SourceCollectJobModel) -> None:
       config = self.get_config()
       state = self.get_state()
       
       # Collect data from external source
       data = await fetch_data(config.api_key)
       
       # Convert to StarGraphForm
       collected = []
       for item in data:
           graph = YourResolver.create_graph(item)
           collected.append(graph)
       
       # Save to database
       with SessionLocal() as db:
           for graph in collected:
               await RootManager.add_star_graph_to_session(graph, db)
           db.commit()
   ```

3. **Implement the `_organize` method**:
   - Called after collection to organize/process collected blocks
   - Often left as a no-op if no post-processing is needed
   
   ```python
   async def _organize(self, block_id: BlockID) -> None:
       """Organize collected block."""
       pass
   ```


### Schema

Schemas define the data models for content stored in blocks.

#### Guidelines for Writing Schemas

1. **Use Pydantic `BaseModel` for content models**:
   ```python
   from pydantic import BaseModel
   from typing import Optional as Opt
   from datetime import datetime
   
   class YourContentModel(BaseModel):
       """Your content description."""
       id: int
       title: str
       content: Opt[str] = None
       created_at: datetime
       # Add other fields
   ```

2. **Keep schemas focused on content only**:
   - Don't include user, chat, or other relational data unless they're core to the content
   - Use relations in `StarGraphForm` to link related entities
   - Store only the essential data that defines the content itself

3. **Add resolver reference**:
   ```python
   import typing
   
   class YourContentModel(BaseModel):
       # ... fields ...
       __resolver__: typing.ClassVar[typing.Any] = None
   ```

4. **Provide good documentation**:
   - Add docstrings to the class and each field
   - Include examples in `model_config` if helpful

### Resolver

Resolvers handle blocks containing your schema's data.

#### Guidelines for Writing Resolvers

1. **Inherit from `Resolver` with resolver type**:
   ```python
   from app.business.info_base.resolver import Resolver
   from app.schemas.info_base.block import BlockModel
   from app.schemas.info_base.main import StarGraphForm
   
   class YourResolver(Resolver, rso_type="your_resolver_type"):
       """Resolver for your content blocks."""
       
       def __post_init__(self):
           """Parse content after initialization."""
           self.content = YourContentModel.model_validate_json(self._block.content)
   ```

2. **Implement `create_graph` class method**:
   - Factory method to create `StarGraphForm` from your content model
   - Include any relations (in_relations, out_relations) to connect entities
   
   ```python
   @classmethod
   def create_graph(cls, content: YourContentModel) -> StarGraphForm:
       """Create a StarGraphForm from content data.
       
       :param content: Content object to convert to block
       :return: StarGraphForm for the content
       """
       return StarGraphForm(
           block=BlockModel(
               resolver=cls.__rsotype__,
               content=content.model_dump_json(),
           ),
           out_relations=(),  # Add relations if needed
       )
   ```

3. **Implement text methods**:
   - `async def get_text(self) -> str`: Returns human-readable text representation
   - `def get_str_for_embedding(self) -> str`: Returns text optimized for semantic search
   
   ```python
   async def get_text(self) -> str:
       """Get text representation of the content."""
       return self.content.title or "[no title]"
   
   def get_str_for_embedding(self) -> str:
       """Get text for embedding generation."""
       parts = []
       if self.content.title:
           parts.append(f"Title: {self.content.title}")
       if self.content.content:
           parts.append(self.content.content)
       return "\n".join(parts)
   ```

4. **Register resolver with schema**:
   ```python
   # At the end of resolver.py
   YourContentModel.__resolver__ = YourResolver
   ```

5. **Implement `get_existing` if needed**:
   - Override to check if block with same content already exists
   - Return `None` if uniqueness check not needed
   
   ```python
   def get_existing(self, db_session: Session) -> BlockModel | None:
       """Check if block already exists."""
       return None  # Or implement uniqueness check
   ```

### Storage

Storage type has to follow `extensions.{extension_id}.{type}` pattern.

### Extension Registration

In your extension's `__init__.py`:

```python
from app.business.extension.main import ExtensionBase

class Extension(
    ExtensionBase[YourExtensionConfig],
    ext_id="your_extension_id",
    config_cls=YourExtensionConfig,
):
    """Your extension description."""
    
    @classmethod
    def _init_resolvers(cls):
        """Initialize resolvers."""
        from .resolver import YourResolver  # noqa: F401
    
    @classmethod
    def _init_sources(cls):
        """Initialize sources."""
        from .source import Source  # noqa: F401
    
    @classmethod
    def _register_apis(cls, router: APIRouter):
        """Register API endpoints."""
        from app.business.source import SourceManager
        
        router.post("/your_endpoint")(
            lambda nickname: SourceManager.create(
                f"extensions.{cls.__extid__}.source.Source", nickname
            )
        )
```

## Examples

See the following built-in extensions for reference:
- **mail**: IMAP email collection with EmailAddress relations
- **telegram**: Telegram bot message collection with simplified schema