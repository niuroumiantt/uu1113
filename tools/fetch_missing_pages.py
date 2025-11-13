import os
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

BASE_URL = "https://uvation.com"

def project_root():
    # tools/ is one level below repo root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def site_root():
    # Use standardized sites/ structure as single source of truth
    return os.path.join(project_root(), "sites", "uvation.com", "public")

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; TraeFetcher/1.0; +https://uvation.com)"
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def parse_sitemap_xml(xml_bytes):
    urls = []
    root = ET.fromstring(xml_bytes)
    tag = root.tag.lower()
    # Handle sitemapindex and urlset
    if tag.endswith('sitemapindex'):
        for sm in root.findall("{*}sitemap"):
            loc_el = sm.find("{*}loc")
            if loc_el is not None and loc_el.text:
                try:
                    sub_xml = fetch(loc_el.text.strip())
                    urls.extend(parse_sitemap_xml(sub_xml))
                except Exception as e:
                    print(f"[WARN] Failed to fetch sub-sitemap {loc_el.text}: {e}")
    elif tag.endswith('urlset'):
        for u in root.findall("{*}url"):
            loc_el = u.find("{*}loc")
            if loc_el is not None and loc_el.text:
                urls.append(loc_el.text.strip())
    else:
        # Fallback: attempt to read all <loc>
        for loc_el in root.findall(".//{*}loc"):
            if loc_el.text:
                urls.append(loc_el.text.strip())
    return urls

def url_to_local_path(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc and parsed.netloc != urllib.parse.urlparse(BASE_URL).netloc:
        return None  # ignore other domains
    path = parsed.path or "/"
    # Normalize: ensure leading slash only once
    if not path.startswith("/"):
        path = "/" + path
    # Decide filename
    dirname, filename = None, None
    # If path endswith / -> index.html
    if path.endswith("/"):
        dirname = path.lstrip("/")
        filename = "index.html"
    else:
        # If has extension -> use as-is, else treat as directory index
        base = os.path.basename(path)
        if "." in base:
            dirname = os.path.dirname(path).lstrip("/")
            filename = base
        else:
            dirname = path.lstrip("/")
            filename = "index.html"
    local_dir = os.path.join(site_root(), dirname) if dirname else site_root()
    local_path = os.path.join(local_dir, filename)
    return local_path

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def main():
    start = time.time()
    print("[INFO] Fetching sitemap.xml from online site...")
    try:
        xml = fetch(BASE_URL + "/sitemap.xml")
    except Exception as e:
        print(f"[ERROR] Failed to fetch sitemap.xml: {e}")
        sys.exit(1)

    print("[INFO] Parsing sitemap...")
    urls = parse_sitemap_xml(xml)
    urls = [u for u in urls if u and u.startswith(BASE_URL)]
    print(f"[INFO] Total URLs in sitemap: {len(urls)}")

    missing = []
    downloaded = 0
    for u in urls:
        local_path = url_to_local_path(u)
        if not local_path:
            continue
        if os.path.exists(local_path):
            continue
        missing.append((u, local_path))

    report_dir = os.path.join(site_root(), "_download_reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "missing_pages.txt")
    with open(report_path, "w") as f:
        for u, lp in missing:
            f.write(f"{u} => {lp}\n")
    print(f"[INFO] Missing pages count: {len(missing)} (report: {report_path})")

    for u, local_path in missing:
        try:
            print(f"[DL ] {u}")
            body = fetch(u)
            ensure_dir(local_path)
            with open(local_path, "wb") as out:
                out.write(body)
            downloaded += 1
        except Exception as e:
            print(f"[WARN] Failed to download {u}: {e}")

    elapsed = time.time() - start
    print(f"[DONE] Downloaded {downloaded}/{len(missing)} missing pages in {elapsed:.1f}s")

if __name__ == "__main__":
    main()