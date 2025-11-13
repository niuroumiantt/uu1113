#!/usr/bin/env python3
import os
import re
import json
import time
from urllib.parse import urljoin

import requests


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sites', 'uvation.com', 'public'))
BASE_URL = 'http://localhost:5504/'
REPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sites', 'uvation.com', 'reports'))


EXTERNAL_IGNORED_HOSTS = (
    'googletagmanager.com',
    'google-analytics.com',
    'analytics.google.com',
    'google.com/ccm',
    'clarity.ms',
    'px.ads.linkedin.com',
    'licdn.com',
    'amplitude.com',
)


def is_local_resource(url: str) -> bool:
    if not url:
        return False
    # consider URLs starting with '/', './', '../' as local
    return url.startswith('/') or url.startswith('./') or url.startswith('../')


def is_external_ignored(url: str) -> bool:
    if not url:
        return False
    return any(host in url for host in EXTERNAL_IGNORED_HOSTS)


def extract_resource_urls(html: str) -> dict:
    urls = {
        'link': [],
        'script': [],
        'img': [],
        'source': [],
    }
    # rudimentary extraction using regex for robustness without external deps
    for attr, tag in [('href', 'link'), ('src', 'script')]:
        pattern = re.compile(rf'<{tag}[^>]*{attr}=["\']([^"\']+)["\']', re.IGNORECASE)
        urls[tag].extend(pattern.findall(html))
    # images
    img_pattern = re.compile(r'<img[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
    urls['img'].extend(img_pattern.findall(html))
    # source tags (video/picture)
    source_src_pattern = re.compile(r'<source[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
    urls['source'].extend(source_src_pattern.findall(html))
    # srcset parsing (multiple URLs separated by commas)
    srcset_pattern = re.compile(r'(?:srcset|data-srcset)=["\']([^"\']+)["\']', re.IGNORECASE)
    for srcset in srcset_pattern.findall(html):
        parts = [p.strip().split(' ')[0] for p in srcset.split(',')]
        urls['source'].extend(parts)
    return urls


def check_url(url: str) -> tuple:
    try:
        # prefer HEAD to reduce bandwidth; fallback to GET if not allowed
        resp = requests.head(url, timeout=10)
        if resp.status_code in (405, 403):
            resp = requests.get(url, timeout=15, stream=True)
        return True, resp.status_code, None
    except Exception as e:
        return False, None, str(e)


def enumerate_index_pages(base_dir: str) -> list:
    pages = []
    # root index.html
    root_index = os.path.join(base_dir, 'index.html')
    if os.path.exists(root_index):
        pages.append('/')
    # nested index.html
    for root, dirs, files in os.walk(base_dir):
        if 'index.html' in files:
            rel = os.path.relpath(root, base_dir)
            if rel == '.':
                continue
            # normalize to URL path
            url_path = '/' + rel.strip('/') + '/'
            pages.append(url_path)
    return sorted(set(pages))


def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    summary = {
        'base_dir': BASE_DIR,
        'base_url': BASE_URL,
        'generated_at': int(time.time()),
        'pages': [],
    }

    pages = enumerate_index_pages(BASE_DIR)
    for path in pages:
        page_url = urljoin(BASE_URL, path.lstrip('/'))
        page_result = {
            'path': path,
            'url': page_url,
            'status': None,
            'ok': False,
            'missing_resources': [],
            'external_ignored': 0,
            'checked_resources': 0,
        }
        ok, code, err = check_url(page_url)
        page_result['status'] = code
        page_result['ok'] = ok and code and code < 400

        if not page_result['ok']:
            summary['pages'].append(page_result)
            continue

        try:
            html = requests.get(page_url, timeout=15).text
        except Exception as e:
            page_result['ok'] = False
            page_result['status'] = None
            page_result['missing_resources'].append({'type': 'page', 'url': page_url, 'error': str(e)})
            summary['pages'].append(page_result)
            continue

        urls = extract_resource_urls(html)
        # flatten
        all_resources = []
        for t, lst in urls.items():
            for u in lst:
                all_resources.append((t, u))

        for rtype, rurl in all_resources:
            if is_external_ignored(rurl):
                page_result['external_ignored'] += 1
                continue
            if not is_local_resource(rurl):
                # skip other external resources
                continue
            # resolve to absolute URL relative to page_url
            abs_url = urljoin(page_url, rurl)
            ok, code, err = check_url(abs_url)
            page_result['checked_resources'] += 1
            if not ok or (code and code >= 400):
                page_result['missing_resources'].append({
                    'type': rtype,
                    'url': abs_url,
                    'status': code,
                    'error': err,
                })

        summary['pages'].append(page_result)

    # write reports
    json_path = os.path.join(REPORT_DIR, 'validation_report.json')
    md_path = os.path.join(REPORT_DIR, 'validation_report.md')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # markdown summary
    lines = []
    lines.append(f"Base URL: {BASE_URL}")
    lines.append(f"Pages checked: {len(summary['pages'])}")
    total_missing = sum(len(p['missing_resources']) for p in summary['pages'])
    lines.append(f"Total missing local resources: {total_missing}")
    lines.append("")
    for p in summary['pages']:
        status = p['status'] if p['status'] is not None else 'ERR'
        lines.append(f"- {p['path']} ({status}), checked {p['checked_resources']} resources, ignored external {p['external_ignored']}")
        for m in p['missing_resources'][:10]:  # cap output
            lines.append(f"  - missing {m['type']}: {m['url']} (status={m['status']}, err={m['error']})")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Wrote reports:\n- {json_path}\n- {md_path}")


if __name__ == '__main__':
    main()