#!/bin/bash
set -e

PROJECT_DIR="/home/AvondjeUit/volgsysteem/volgsysteem_au"
PYTHON="$PROJECT_DIR/env/bin/python"

cd "$PROJECT_DIR"

"$PYTHON" manage.py ververs_weeztix_token

sudo systemctl restart gunicorn.service