- Use `fastapi.openapi.utils.get_openapi`, we can generate OpenAPI Spec automatically from code.
- This required to import `run` and which will sync extensions, and so requires DB connection.
  But this can be furstrating and unneeded since OpenAPI spec is generated at development stage,
  not runtime, so add an env var `IN_CI`.