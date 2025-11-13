#!/usr/bin/env python3
import http.server
import socketserver
import os
import io
import sys
import urllib.parse
import urllib.request

# Base directory to serve
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sites", "uvation.com", "public"))

INJECTION_SNIPPET = """
<script>(function(){try{
window.dataLayer=window.dataLayer||[];
if(typeof window.dataLayer.on!=="function"){window.dataLayer.on=function(){}};
window.gtag=window.gtag||function(){};
window.ga=window.ga||function(){};
window.clarity=window.clarity||function(){};
window.lintrk=window.lintrk||function(){};
window._linkedin_partner_id=window._linkedin_partner_id||"0";
// Suppress known third-party errors to avoid local preview overlay
window.addEventListener('error',function(e){var msg=String(e.message||'');
if(/googletagmanager|google-analytics|adservices|clarity|linkedin|cms\.uvation\.com|clearbit/gi.test(msg)){e.preventDefault&&e.preventDefault();e.stopPropagation&&e.stopPropagation();}},true);
// Swallow unhandled rejections commonly caused by blocked external fetches
window.addEventListener('unhandledrejection',function(e){try{var r=e.reason||{};var m=String(r.message||r||'');if(/network|fetch|cors|blocked|googletagmanager|analytics|cms\.uvation\.com/gi.test(m)){e.preventDefault&&e.preventDefault();e.stopPropagation&&e.stopPropagation();}}catch(_){}});
// Remove Next.js production error banner if present
document.addEventListener('DOMContentLoaded',function(){try{var nodes=document.querySelectorAll('body div, body p');for(var i=0;i<nodes.length;i++){var n=nodes[i];var t=(n.textContent||'').trim();if(/Application error\: a client-side exception has occurred/i.test(t)){n.style.display='none';}}}catch(_){}});
}catch(e){console.warn('local-preview-shim',e)}})();
</script>
"""

class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Map requested path to BASE_DIR
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        trailing_slash = path.rstrip().endswith('/')
        # Normalize
        path = os.path.normpath(urllib.parse.unquote(path))
        full_path = os.path.join(BASE_DIR, path.lstrip('/'))
        if os.path.isdir(full_path) and trailing_slash:
            index_path = os.path.join(full_path, 'index.html')
            if os.path.exists(index_path):
                return index_path
        return full_path

    def _serve_file_bytes(self, fpath):
        try:
            with open(fpath, 'rb') as f:
                return f.read()
        except OSError:
            return None

    def do_GET(self):
        # Lightweight proxy for image-proxy only (common in pages)
        if self.path.startswith('/api/image-proxy'):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            url = qs.get('url', [None])[0]
            if not url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error":"Missing url"}')
                return
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'LocalPreview/1.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                    ctype = resp.headers.get('Content-Type', 'application/octet-stream')
                    self.send_response(200)
                    self.send_header('Content-Type', ctype)
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as e:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(str(e).encode('utf-8'))
            return

        # Default static serving with HTML injection
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            index_path = os.path.join(path, 'index.html')
            if os.path.exists(index_path):
                path = index_path

        data = self._serve_file_bytes(path)
        if data is None:
            self.send_error(404, "File not found")
            return

        ext = os.path.splitext(path)[1].lower()
        if ext in ('.html', '.htm'):
            try:
                text = data.decode('utf-8', errors='ignore')
                # Inject right before </head> to ensure early execution
                if '</head>' in text:
                    text = text.replace('</head>', INJECTION_SNIPPET + '</head>', 1)
                data = text.encode('utf-8')
            except Exception:
                pass
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(data)
            return
        else:
            # Serve as static
            ctype = self.guess_type(path)
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(data)


def main():
    port = int(os.environ.get('PORT', '5504'))
    os.chdir(BASE_DIR)
    with socketserver.TCPServer(("0.0.0.0", port), PreviewHandler) as httpd:
        print(f"Serving {BASE_DIR} on http://localhost:{port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()