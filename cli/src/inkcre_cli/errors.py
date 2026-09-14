"""Command failures, separate from successfully observed domain outcomes."""

from typing import Any


class CommandError(Exception):
    def __init__(self, detail: Any, *, status: int | None = None, exit_code: int = 1):
        super().__init__(str(detail))
        self.detail = detail
        self.status = status
        self.exit_code = exit_code

    def as_dict(self) -> dict[str, Any]:
        result = {"detail": self.detail}
        if self.status is not None:
            result["http_status"] = self.status
        return result
