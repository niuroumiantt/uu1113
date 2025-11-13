#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.parse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PUBLIC_DIR = os.path.join(REPO_ROOT, 'sites', 'uvation.com', 'public')
REPORT_JSON = os.path.join(REPO_ROOT, 'sites', 'uvation.com', 'reports', 'validation_report.json')

REMOTE_BASE = 'https://uvation.com'
LOCAL_BASE = 'http://localhost:5504'


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; TraeSync/1.0)'
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def save(path: str, data: bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def to_remote_and_local_paths(url: str):
    # url is like http://localhost:5504/_next/static/...; map to REMOTE_BASE and local filesystem
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or '/'
    remote_url = urllib.parse.urljoin(REMOTE_BASE, path)
    local_path = os.path.join(PUBLIC_DIR, path.lstrip('/'))
    return remote_url, local_path


def main():
    if not os.path.exists(REPORT_JSON):
        print(f"[ERROR] Report not found: {REPORT_JSON}")
        return 1
    with open(REPORT_JSON, 'r', encoding='utf-8') as f:
        report = json.load(f)

    # Collect unique missing local resource URLs
    resources = set()
    for p in report.get('pages', []):
        for m in p.get('missing_resources', []):
            u = m.get('url')
            t = m.get('type')
            if not u or t == 'page':
                continue
            # Only process local-base URLs
            if u.startswith(LOCAL_BASE):
                resources.add(u)

    print(f"[INFO] Missing resource URLs to attempt: {len(resources)}")
    downloaded = 0
    exists = 0
    failed = 0
    for u in sorted(resources):
        remote, local = to_remote_and_local_paths(u)
        if os.path.exists(local):
            exists += 1
            print(f"exists: {local}")
            continue
        try:
            data = fetch(remote)
            save(local, data)
            downloaded += 1
            print(f"downloaded: {remote} -> {local}")
        except Exception as e:
            failed += 1
            print(f"failed: {remote} :: {e}")

    print(f"[DONE] downloaded={downloaded}, exists={exists}, failed={failed}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())