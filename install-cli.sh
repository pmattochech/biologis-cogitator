#!/usr/bin/env bash
# Back-compat wrapper — prefer ./install.sh
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install.sh" "$@"
