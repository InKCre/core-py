#!/bin/sh
set -eu

export PGRST_SERVER_HOST="${PGRST_SERVER_HOST:-0.0.0.0}"
export PGRST_SERVER_PORT="${PORT:-${PGRST_SERVER_PORT:-3000}}"

exec postgrest
