#!/usr/bin/env python3
import os
import sys
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PUBLIC_DIR = os.path.join(REPO_ROOT, 'sites', 'uvation.com', 'public')
REMOTE_BASE = 'https://uvation.com'


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; TraeFetchAsset/1.0)'
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/fetch_asset.py /_next/static/chunks/<file>.js [more ...]")
        return 1
    for rel in sys.argv[1:]:
        if not rel.startswith('/'):
            print(f"[SKIP] Not an absolute path: {rel}")
            continue
        remote = REMOTE_BASE + rel
        local = os.path.join(PUBLIC_DIR, rel.lstrip('/'))
        os.makedirs(os.path.dirname(local), exist_ok=True)
        try:
            data = fetch(remote)
            with open(local, 'wb') as f:
                f.write(data)
            print(f"downloaded: {remote} -> {local}")
        except Exception as e:
            print(f"failed: {remote} :: {e}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())