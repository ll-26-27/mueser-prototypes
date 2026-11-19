#!/bin/sh
# Page count before and after. Needs LibreOffice. Run from the repository root.
uv run python -m mueser.style cv check --before "$1" --after "$2"
