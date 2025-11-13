#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
REPORT_DIR="$REPO_ROOT/sites/uvation.com/reports"

echo "[1/4] Validate pages (pre-sync)"
python3 "$REPO_ROOT/tools/validate_pages.py"

echo "[2/4] Backup pre-sync reports"
cp "$REPORT_DIR/validation_report.md" "$REPORT_DIR/validation_report.before_sync.md"
cp "$REPORT_DIR/validation_report.json" "$REPORT_DIR/validation_report.before_sync.json"

echo "[3/4] Sync missing assets from report"
python3 "$REPO_ROOT/tools/sync_assets_from_report.py"

echo "[4/4] Validate pages (post-sync)"
python3 "$REPO_ROOT/tools/validate_pages.py"

echo "[5/5] Compare reports"
python3 "$REPO_ROOT/tools/compare_validation_reports.py"

echo "[DONE] See: $REPORT_DIR/validation_compare.md"