#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 tools/validate_v3.py
python3 tools/validate_integrity_v4.py
python3 tools/story_engine_v4.py
python3 tools/build_preview_v4.py
python3 -m unittest discover -s tests -v
printf 'Offline checks passed. UE5 build unverified.\n'
