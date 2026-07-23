"""Convert a cookie header from standard input to JSON."""

import json
import sys


def cookie_string_to_json(cookie_string: str) -> dict[str, str]:
  """Parse semicolon-delimited cookie pairs."""
  cookies: dict[str, str] = {}
  for cookie in cookie_string.split(";"):
    cookie = cookie.strip()
    if "=" in cookie:
      name, value = cookie.split("=", 1)
      cookies[name.strip()] = value.strip()
  return cookies


def main() -> int:
  """Read a cookie header from stdin and emit JSON."""
  cookie_string = sys.stdin.read().strip()
  if not cookie_string:
    print("Error: No cookie string provided via stdin.", file=sys.stderr)
    return 1

  print(json.dumps(cookie_string_to_json(cookie_string), indent=2))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
