#!/usr/bin/env python3
import os
import re
import shutil
from typing import Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(REPO_ROOT, 'sites', 'uvation.com', 'public')
DST_DIR = os.path.join(REPO_ROOT, 'sites', 'uvation.com', 'public_sanitized')

# Domains/substrings to block in local preview to reduce third-party noise
BLOCK_SUBSTRINGS = [
    'googletagmanager.com',
    'googleadservices.com',
    'analytics.google.com',
    'clarity.ms',
    'google.com/ccm',
    'snap.licdn.com',
    'linkedin.com',
    'amplitude.com',
    'gstatic.com/call-tracking',
    'px.ads.linkedin.com',
    'google.co.kr/ads/ga-audiences',
]

SCRIPT_TAG_RE = re.compile(r'<script[^>]+src=["\"]([^"\"]+)["\"][^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
SCRIPT_INLINE_RE = re.compile(r'<script(?![^>]+src)[^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)
IMG_TAG_RE = re.compile(r'<img[^>]+src=["\"]([^"\"]+)["\"][^>]*>', re.IGNORECASE)
LINK_TAG_RE = re.compile(r'<link[^>]+href=["\"]([^"\"]+)["\"][^>]*>', re.IGNORECASE)
IFRAME_TAG_RE = re.compile(r'<iframe[^>]+src=["\"]([^"\"]+)["\"][^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL)

INLINE_BLOCK_KEYWORDS = [
    'googletagmanager.com', 'gtag(', 'GTM-', 'dataLayer',
    'clarity', 'amplitude', 'linkedin', 'adsbygoogle',
]


def sanitize_html(text: str) -> Tuple[str, int]:
    removed = 0

    def block_url(url: str) -> bool:
        return any(sub in url for sub in BLOCK_SUBSTRINGS)

    def repl_script(m: re.Match) -> str:
        nonlocal removed
        src = m.group(1)
        # Only block known third-party scripts; allow local Next.js runtime
        if block_url(src):
            removed += 1
            return ''
        return m.group(0)

    def repl_img(m: re.Match) -> str:
        nonlocal removed
        src = m.group(1)
        if block_url(src):
            removed += 1
            return ''
        return m.group(0)

    def repl_link(m: re.Match) -> str:
        nonlocal removed
        href = m.group(1)
        if block_url(href):
            removed += 1
            return ''
        return m.group(0)

    def repl_iframe(m: re.Match) -> str:
        nonlocal removed
        src = m.group(1)
        if block_url(src):
            removed += 1
            return ''
        return m.group(0)

    def repl_inline(m: re.Match) -> str:
        nonlocal removed
        body = m.group(1)
        if any(k in body for k in INLINE_BLOCK_KEYWORDS):
            removed += 1
            return ''
        return m.group(0)

    text = SCRIPT_TAG_RE.sub(repl_script, text)
    text = SCRIPT_INLINE_RE.sub(repl_inline, text)
    text = IMG_TAG_RE.sub(repl_img, text)
    text = LINK_TAG_RE.sub(repl_link, text)
    text = IFRAME_TAG_RE.sub(repl_iframe, text)
    # Inject restrictive CSP to block unexpected external loads in preview
    csp = (
        "<meta http-equiv=\"Content-Security-Policy\" "
        "content=\"default-src 'self'; "
        "script-src 'self' 'unsafe-inline' blob:; "
        "style-src 'self' 'unsafe-inline' https:; "
        "img-src 'self' data: blob: https://cdn.uvation.com https://cms.uvation.com; "
        "font-src 'self' data: blob: https://1.www.s81c.com; "
        "connect-src 'self' data: blob:; "
        "frame-src 'self' data:;\">"
    )
    if '<head' in text:
        text = re.sub(r'<head[^>]*>', lambda m: m.group(0) + csp, text, count=1, flags=re.IGNORECASE)
    else:
        text = csp + text
    # Keep preview minimal; do not inject additional UI banners
    return text, removed


def copy_and_sanitize(src_root: str, dst_root: str) -> Tuple[int, int]:
    if os.path.exists(dst_root):
        shutil.rmtree(dst_root)
    os.makedirs(dst_root, exist_ok=True)

    total_html = 0
    total_removed = 0
    for root, dirs, files in os.walk(src_root):
        rel_root = os.path.relpath(root, src_root)
        dst_dir = os.path.join(dst_root, rel_root) if rel_root != '.' else dst_root
        os.makedirs(dst_dir, exist_ok=True)
        for name in files:
            src_path = os.path.join(root, name)
            dst_path = os.path.join(dst_dir, name)
            if name.endswith('.html'):
                try:
                    with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                    sanitized, removed = sanitize_html(text)
                    with open(dst_path, 'w', encoding='utf-8') as f:
                        f.write(sanitized)
                    total_html += 1
                    total_removed += removed
                except Exception as e:
                    print(f"[WARN] HTML sanitize skip {src_path}: {e}")
            else:
                try:
                    shutil.copy2(src_path, dst_path)
                except Exception as e:
                    print(f"[WARN] Copy skip {src_path}: {e}")
    return total_html, total_removed


def main():
    print(f"[INFO] Sanitizing preview: {SRC_DIR} -> {DST_DIR}")
    total_html, total_removed = copy_and_sanitize(SRC_DIR, DST_DIR)
    print(f"[DONE] HTML files processed: {total_html}, tags removed: {total_removed}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())