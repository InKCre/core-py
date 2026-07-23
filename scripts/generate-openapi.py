import json
import os
import sys

# Add the parent directory to sys.path to import run
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.openapi.utils import get_openapi
from run import api_app

openapi_schema = get_openapi(
  title=api_app.title,
  version=api_app.version,
  description=api_app.description,
  routes=api_app.routes,
)
with open("docs/openapi.json", "w", encoding="utf-8") as f:
  json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
print("OpenAPI schema generated successfully")
