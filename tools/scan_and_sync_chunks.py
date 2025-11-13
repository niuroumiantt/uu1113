#!/usr/bin/env python3
import os
import re
import urllib.request
from typing import Set

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PUBLIC_DIR = os.path.join(REPO_ROOT, 'sites', 'uvation.com', 'public')
REMOTE_BASE = 'https://uvation.com'

CHUNK_PATTERNS = [
    r"/_next/static/chunks/[A-Za-z0-9]+\.js",
    r"/_next/static/chunks/[A-Za-z0-9]+\.css",
]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; TraeChunkSync/1.0)'
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def save(path: str, data: bytes):
    ensure_dir(os.path.dirname(path))
    with open(path, 'wb') as f:
        f.write(data)


def scan_files_for_chunks(base_dir: str) -> Set[str]:
    found: Set[str] = set()
    for root, dirs, files in os.walk(base_dir):
        for name in files:
            # only scan likely text assets
            if not (name.endswith('.html') or name.endswith('.js') or name.endswith('.css')):
                continue
            file_path = os.path.join(root, name)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                for pat in CHUNK_PATTERNS:
                    for m in re.findall(pat, text):
                        found.add(m)
            except Exception as e:
                print(f"[WARN] Skip {file_path}: {e}")
    return found


def main():
    print(f"[INFO] Scanning for chunk references in {PUBLIC_DIR}")
    refs = scan_files_for_chunks(PUBLIC_DIR)
    print(f"[INFO] Total chunk references found: {len(refs)}")

    downloaded = 0
    exists = 0
    failed = 0
    for rel in sorted(refs):
        local_path = os.path.join(PUBLIC_DIR, rel.lstrip('/'))
        remote_url = REMOTE_BASE + rel
        if os.path.exists(local_path):
            exists += 1
            # print(f"exists: {local_path}")
            continue
        try:
            data = fetch(remote_url)
            save(local_path, data)
            downloaded += 1
            print(f"downloaded: {remote_url} -> {local_path}")
        except Exception as e:
            failed += 1
            print(f"failed: {remote_url} :: {e}")

    print(f"[DONE] downloaded={downloaded}, exists={exists}, failed={failed}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())