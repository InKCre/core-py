"""Native dynamic-input errors at ordinary REST boundaries."""

import contextlib

import fastapi.exceptions
import jsonschema  # pyrefly: ignore[untyped-import]
import pydantic
import psycopg.errors
from sqlalchemy.exc import IntegrityError


@contextlib.contextmanager
def database_write():
  """Translate database-owned reference/invariant conflicts for an explicit write.

  Do not pre-read referenced rows or repeat CHECK predicates in the adapter.
  This is not a global database-error handler: connection faults, programming
  errors and generated-key collisions still propagate as server failures.
  """
  try:
    yield
  except IntegrityError as error:
    if not isinstance(
      error.orig, (psycopg.errors.ForeignKeyViolation, psycopg.errors.CheckViolation)
    ):
      raise
    detail = {"message": error.orig.diag.message_primary}
    if error.orig.diag.constraint_name:
      detail["constraint"] = error.orig.diag.constraint_name
    raise fastapi.exceptions.HTTPException(409, detail) from error


@contextlib.contextmanager
def request_input(*path: str | int, strip: tuple[str | int, ...] = ()):
  """Map only the enclosed input operation, never Resolver execution/output."""

  def location(parts):
    parts = tuple(parts)
    if strip and parts[: len(strip)] == strip:
      parts = parts[len(strip) :]
    return ("body", *path, *parts)

  try:
    yield
  except pydantic.ValidationError as error:
    details = [
      {**item, "loc": location(item["loc"])} for item in error.errors(include_url=False)
    ]
    raise fastapi.exceptions.RequestValidationError(details) from error
  except jsonschema.ValidationError as error:
    raise fastapi.exceptions.RequestValidationError(
      [
        {
          "loc": location(error.absolute_path),
          "msg": error.message,
          "type": "json_schema",
          "input": error.instance,
        }
      ]
    ) from error
