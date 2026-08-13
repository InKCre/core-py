"""Static artifact catalog remains aligned with executable Core registrations."""

from app.business.job import JobManager
from app.business.lexical_retrieval.job import (  # noqa: F401
  LexicalMaintainJobHandler,
  LexicalRebuildJobHandler,
)
from app.business.organization_job import MediaInterpretationJobHandler  # noqa: F401
from app.business.semantic_retrieval.job import (  # noqa: F401
  SemanticMaintainJobHandler,
  SemanticRebuildJobHandler,
)
from app.business.source.job import (  # noqa: F401
  SourceBackfillJobHandler,
  SourceCollectJobHandler,
)
from app.database_contract.profile import (
  BUILTIN_AI_DIALECTS_BY_ID,
  BUILTIN_JOB_TYPES_BY_ID,
  OPENAI_COMPATIBLE_DIALECT_SCHEMA,
)


def test_every_core_job_registration_matches_the_artifact_catalog() -> None:
  assert set(JobManager._handlers) == set(BUILTIN_JOB_TYPES_BY_ID)
  for job_type, handler in JobManager._handlers.items():
    profile = BUILTIN_JOB_TYPES_BY_ID[job_type]
    assert profile.description == handler.description
    assert profile.parameters_schema == handler.parameters_model.model_json_schema()
    assert profile.default_timeout_seconds == handler.default_timeout_seconds


def test_openai_family_dialects_share_the_artifact_connection_contract() -> None:
  assert BUILTIN_AI_DIALECTS_BY_ID["core.openai-compatible.v1"].config_schema == (
    OPENAI_COMPATIBLE_DIALECT_SCHEMA
  )
  assert BUILTIN_AI_DIALECTS_BY_ID["core.alibaba-model-studio.v1"].config_schema == (
    OPENAI_COMPATIBLE_DIALECT_SCHEMA
  )
