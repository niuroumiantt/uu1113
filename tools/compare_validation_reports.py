#!/usr/bin/env python3
import os
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPORT_DIR = os.path.join(REPO_ROOT, 'sites', 'uvation.com', 'reports')
BEFORE_JSON = os.path.join(REPORT_DIR, 'validation_report.before_sync.json')
AFTER_JSON = os.path.join(REPORT_DIR, 'validation_report.json')
OUT_MD = os.path.join(REPORT_DIR, 'validation_compare.md')


def collect_missing_resources(report):
    miss = set()
    pages = report.get('pages', [])
    for p in pages:
        for m in p.get('missing_resources', []):
            if m.get('type') == 'page':
                continue
            url = m.get('url')
            if url:
                miss.add(url)
    return miss


def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    if not os.path.exists(BEFORE_JSON):
        print(f"[ERROR] Not found before-sync report: {BEFORE_JSON}")
        return 1
    if not os.path.exists(AFTER_JSON):
        print(f"[ERROR] Not found latest report: {AFTER_JSON}")
        return 1

    before = read_json(BEFORE_JSON)
    after = read_json(AFTER_JSON)

    miss_before = collect_missing_resources(before)
    miss_after = collect_missing_resources(after)

    resolved = sorted(miss_before - miss_after)
    still_missing = sorted(miss_after)
    new_missing = sorted(miss_after - miss_before)

    lines = []
    lines.append("Validation Compare Summary")
    lines.append("")
    lines.append(f"Before missing count: {len(miss_before)}")
    lines.append(f"After missing count: {len(miss_after)}")
    lines.append(f"Resolved count: {len(resolved)}")
    lines.append(f"New missing count: {len(new_missing)}")
    lines.append("")
    if resolved:
        lines.append("Resolved resources:")
        for u in resolved:
            lines.append(f"- {u}")
        lines.append("")
    if still_missing:
        lines.append("Still missing resources:")
        for u in still_missing[:50]:
            lines.append(f"- {u}")
        lines.append("")
    if new_missing:
        lines.append("Newly missing resources:")
        for u in new_missing[:50]:
            lines.append(f"- {u}")
        lines.append("")

    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"[DONE] Wrote compare summary: {OUT_MD}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())