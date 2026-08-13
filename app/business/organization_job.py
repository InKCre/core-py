"""Exact automatic Organization commands hosted by Jobs."""

from app.business.job import JobHandler
from app.business.organization import OrganizationManager
from app.business.organization_media import MEDIA_INTERPRETATION_JOB_TYPE
from app.schemas.job import JobModel
from app.schemas.organization import MediaInterpretationJobParameters


class MediaInterpretationJobHandler(
  JobHandler[MediaInterpretationJobParameters],
  job_type=MEDIA_INTERPRETATION_JOB_TYPE,
  description="Interpret missing image, audio, and video Blocks through configured Agents.",
  parameters_model=MediaInterpretationJobParameters,
  default_timeout_seconds=1800,
):
  @classmethod
  def can_handle(cls, parameters: MediaInterpretationJobParameters) -> bool:
    del parameters
    return OrganizationManager.can_interpret_media()

  @classmethod
  async def handle(
    cls,
    job: JobModel,
    parameters: MediaInterpretationJobParameters,
  ) -> None:
    del parameters
    report = await OrganizationManager.interpret_missing_media()
    job.state = report.model_dump(mode="json")
