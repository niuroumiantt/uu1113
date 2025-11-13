#!/usr/bin/env python3
"""
Sync Next.js static assets (chunks/media) from uvation.com into local sites/uvation.com/public/_next/static.

Usage:
  python3 tools/sync_next_assets.py

It fetches HTML for pages in PAGES and downloads any referenced assets that are missing locally.
"""
import os
import re
import sys
import urllib.request
from urllib.parse import urljoin

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SITE_DIR = os.path.join(ROOT, 'sites', 'uvation.com', 'public')
DOWNLOAD_DIR = os.path.join(SITE_DIR, '_download_reports')

PAGES = [
    ('https://uvation.com/', os.path.join(SITE_DIR, 'index.html'), 'home'),
    ('https://uvation.com/about/', os.path.join(SITE_DIR, 'about', 'index.html'), 'about'),
]

ASSET_PATTERNS = [
    r"/_next/static/chunks/[A-Za-z0-9\.]+\.js",
    r"/_next/static/chunks/[A-Za-z0-9\.]+\.css",
    r"/_next/static/media/[A-Za-z0-9\-_.]+\.(?:woff2|woff|ttf|svg|png|jpg)",
]

def fetch_url(url: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        return resp.read()

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_file(path: str, content: bytes):
    ensure_dir(os.path.dirname(path))
    with open(path, 'wb') as f:
        f.write(content)

def parse_assets(html_text: str):
    assets = set()
    for pat in ASSET_PATTERNS:
        for m in re.findall(pat, html_text):
            assets.add(m)
    return sorted(assets)

def download_asset(asset_path: str):
    remote = urljoin('https://uvation.com', asset_path)
    local = os.path.join(SITE_DIR, asset_path.lstrip('/'))
    ensure_dir(os.path.dirname(local))
    if os.path.exists(local):
        return ('exists', asset_path)
    try:
        data = fetch_url(remote)
        save_file(local, data)
        return ('downloaded', asset_path)
    except Exception as e:
        return ('failed', asset_path + f' :: {e}')

def main():
    ensure_dir(DOWNLOAD_DIR)
    total_assets = set()
    results = []
    for url, local_html_path, slug in PAGES:
        try:
            html = fetch_url(url)
            save_file(local_html_path, html)
            dl_report = os.path.join(DOWNLOAD_DIR, f'remote_{slug}.html')
            save_file(dl_report, html)
            assets = parse_assets(html.decode('utf-8', errors='ignore'))
            total_assets.update(assets)
        except Exception as e:
            print(f'[ERROR] Fetch HTML failed for {url}: {e}', file=sys.stderr)
    print(f'Total unique assets referenced: {len(total_assets)}')
    downloaded = 0
    exists = 0
    failed = 0
    for asset in sorted(total_assets):
        status, info = download_asset(asset)
        if status == 'downloaded':
            downloaded += 1
        elif status == 'exists':
            exists += 1
        else:
            failed += 1
        print(f'{status}: {info}')
    print(f'Assets downloaded: {downloaded}, already existed: {exists}, failed: {failed}')

if __name__ == '__main__':
    main()