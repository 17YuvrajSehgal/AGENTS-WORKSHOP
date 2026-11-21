import hashlib, io, json, logging, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit

logging.disable(logging.CRITICAL)
from jellyfin_apiclient_python import JellyfinClient

BLOB = bytes((i * 7 + 3) % 256 for i in range(200_000))


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _handle(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        path = urlsplit(self.path).path
        if path.startswith("/Audio/"):
            return self._send(200, BLOB, "application/octet-stream")
        if path.startswith("/Fail500"):
            return self._send(500, b"{}")
        payload = {"path": path, "method": self.command,
                   "Items": [{"Id": "%s-%d" % (path, i), "Name": "n%d" % i} for i in range(20)]}
        return self._send(200, json.dumps(payload).encode())

    do_GET = do_POST = do_DELETE = do_HEAD = _handle


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    url = "http://127.0.0.1:%d" % srv.server_address[1]

    client = JellyfinClient()
    client.config.app("bench", "0.0.1", "machine", "dev-id")
    client.config.data["auth.ssl"] = False
    client.config.data["auth.server"] = url
    client.config.data["auth.user_id"] = "user1"
    client.config.data["auth.token"] = "tok"

    h = hashlib.sha256()
    for i in range(150):
        r = client.jellyfin.get_system_info()
        h.update(json.dumps(r, sort_keys=True).encode())
        r = client.jellyfin.get_item("item%d" % i)
        h.update(json.dumps(r, sort_keys=True).encode())
        r = client.jellyfin.get_user("u%d" % i)
        h.update(json.dumps(r, sort_keys=True).encode())
        r = client.jellyfin.search_media_items(term="t%d" % i, media="Videos")
        h.update(json.dumps(r, sort_keys=True).encode())
        r = client.jellyfin.close_transcode("dev%d" % i)
        h.update(json.dumps(r, sort_keys=True).encode())
        r = client.http.request({"type": "POST", "handler": "Sessions/Playing",
                                 "json": {"ItemId": "{UserId}", "n": i}})
        h.update(json.dumps(r, sort_keys=True).encode())
        r = client.http.request({"type": "GET", "handler": "Fail500"})
        h.update(repr(r).encode())
        if i % 5 == 0:
            buf = io.BytesIO()
            client.http.request({"type": "GET", "handler": "Audio/a%d/universal" % i, "params": {"UserId": "{UserId}", "Container": "mp3"}}, dest_file=buf)
            h.update(hashlib.sha256(buf.getvalue()).digest())
        h.update(client.http.request_url({"handler": "Items/{UserId}", "params": {"x": i}}).split("127.0.0.1:")[1].split("/", 1)[1].encode())
    client.stop()
    srv.shutdown()
    print(h.hexdigest())


main()
