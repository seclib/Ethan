import http.server
import json
import threading

from core.applications.github_organization_discovery import discover_github_org_repositories, GitHubOrgDiscoveryError


def _serve(pages):
    received = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            received.append(self.path)
            if self.path.startswith("/orgs/seclib/repos"):
                page = 1
                if "page=2" in self.path:
                    page = 2
                if page <= len(pages) and pages[page - 1]:
                    body = json.dumps(pages[page - 1]).encode()
                    self.send_response(200)
                    if page < len(pages):
                        link = f'<http://127.0.0.1:{self.server.server_address[1]}/orgs/seclib/repos?page={page + 1}&per_page=1>; rel="next"'
                        self.send_header("Link", link)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                body = json.dumps([]).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    return server, thread, base_url, received


def test_discovers_multiple_pages():
    server, thread, base_url, received = _serve(
        [[{"name": "one", "full_name": "seclib/one", "html_url": "u1", "clone_url": "c1", "topics": ["ai"]}],
         [{"name": "two", "full_name": "seclib/two", "html_url": "u2", "clone_url": "c2"}]]
    )
    try:
        repos = discover_github_org_repositories("seclib", base_url=base_url, per_page=1, access_token=None)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    assert [repo.name for repo in repos] == ["one", "two"]
    assert repos[0].topics == ("ai",)
    assert any("page=2" in path for path in received)


def test_malformed_payload_raises():
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"{not-json"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.join() if False else thread.start()
    try:
        try:
            discover_github_org_repositories("seclib", base_url=f"http://127.0.0.1:{server.server_address[1]}")
            raise AssertionError("Expected GitHubOrgDiscoveryError")
        except GitHubOrgDiscoveryError:
            pass
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
