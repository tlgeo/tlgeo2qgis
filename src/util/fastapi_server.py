"""
Lightweight HTTP server for TLGeo QGIS plugin.
Uses Python stdlib only — no FastAPI, Starlette, Pydantic, or Uvicorn dependencies.
"""
import http.server
import socketserver
import threading
import json
import tempfile
import shutil
import os
from urllib.parse import parse_qs

# Removed QgsMessageLog to ensure thread safety
def log_msg(msg: str):
    print(f"[TLGeoHTTP] {msg}")

server = None
_server_thread = None
_qgis_plugin = None

def _detect_base_port():
    """QGIS 3 → 13000, QGIS 4 → 14000, so both can run side-by-side."""
    try:
        from qgis.core import Qgis
        return 14000 if Qgis.versionInt() >= 40000 else 13000
    except Exception:
        return 13000

BASE_PORT = _detect_base_port()
MAX_PORT_RETRIES = 10
PORT = BASE_PORT  # Will be updated to the actual bound port


def _parse_multipart(body: bytes, boundary: str):
    """Parse multipart/form-data body without external dependencies.

    Works on Python 3.9–3.13+ (does not use the deprecated ``cgi`` module).

    Returns:
        fields: dict of name -> value (str)
        files: list of (name, filename, data: bytes)
    """
    delimiter = f"--{boundary}".encode()
    parts = body.split(delimiter)

    fields = {}
    files = []

    for part in parts:
        # Skip preamble, epilogue, and closing delimiter
        if not part or part.strip() in (b"", b"--", b"--\r\n"):
            continue

        # Remove leading \r\n
        if part.startswith(b"\r\n"):
            part = part[2:]

        # Split headers from body at the first double CRLF
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue

        header_text = part[:header_end].decode("utf-8", errors="replace")
        body_data = part[header_end + 4:]

        # Remove trailing \r\n from body
        if body_data.endswith(b"\r\n"):
            body_data = body_data[:-2]

        # Parse Content-Disposition header
        name = None
        filename = None
        for line in header_text.split("\r\n"):
            if line.lower().startswith("content-disposition:"):
                for param in line.split(";"):
                    param = param.strip()
                    if param.startswith("name="):
                        name = param.split("=", 1)[1].strip('"')
                    elif param.startswith("filename="):
                        filename = param.split("=", 1)[1].strip('"')

        if filename is not None:
            files.append((name, filename, body_data))
        elif name is not None:
            fields[name] = body_data.decode("utf-8", errors="replace")

    return fields, files


def get_plugin():
    import sys
    plugin = getattr(sys, 'tlgeo_plugin', None)
    if plugin is None:
        global _qgis_plugin
        return _qgis_plugin
    return plugin


class TLGeoRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the TLGeo QGIS plugin local server."""

    def log_message(self, format, *args):
        """Override to use our own logger instead of stderr."""
        log_msg(f"{self.client_address[0]} - {format % args}")

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    def _send_json_response(self, data, status=200):
        """Send a JSON response with CORS headers."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self):
        """Add CORS headers to allow cross-origin requests."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    # ------------------------------------------------------------------
    # Request body helpers
    # ------------------------------------------------------------------

    def _read_body(self):
        """Read the raw request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            return self.rfile.read(length)
        return b""

    def _parse_request_body(self):
        """Parse request body based on Content-Type header.

        Supports application/json, application/x-www-form-urlencoded,
        multipart/form-data (fields only), and falls back to raw bytes.
        """
        content_type = self.headers.get("Content-Type", "")
        raw = self._read_body()

        if "application/json" in content_type:
            return json.loads(raw) if raw else {}
        elif "multipart/form-data" in content_type:
            boundary = None
            for part in content_type.split(";"):
                part = part.strip()
                if part.startswith("boundary="):
                    boundary = part.split("=", 1)[1].strip('"')
                    break
            if boundary:
                fields, _ = _parse_multipart(raw, boundary)
                return fields
            return {}
        elif "application/x-www-form-urlencoded" in content_type:
            decoded = raw.decode("utf-8", errors="replace")
            parsed = parse_qs(decoded)
            return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        else:
            return raw

    # ------------------------------------------------------------------
    # HTTP method handlers
    # ------------------------------------------------------------------

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]  # Strip query string

        if path == "/":
            try:
                plugin = get_plugin()
                if not plugin:
                    self._send_json_response({"error": "Plugin not initialized"}, 500)
                    return
                result = plugin.hello()
                self._send_json_response(result)
            except Exception as e:
                log_msg(f"Error in GET /: {e}")
                self._send_json_response({"error": str(e)}, 500)
        else:
            self._send_json_response({"error": "Not found"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]

        if path == "/":
            self._handle_command()
        elif path == "/geotagged_photos":
            self._handle_geotagged_photos()
        elif path == "/geojson":
            self._handle_geojson()
        else:
            self._send_json_response({"error": "Not found"}, 404)

    # ------------------------------------------------------------------
    # Endpoint handlers
    # ------------------------------------------------------------------

    def _handle_command(self):
        try:
            log_msg("POST /")
            body = self._parse_request_body()
            plugin = get_plugin()
            if not plugin:
                self._send_json_response({"error": "Plugin not initialized"}, 500)
                return
            result = plugin.process_command(body)
            self._send_json_response(result)
        except Exception as e:
            log_msg(f"Error in command endpoint: {e}")
            self._send_json_response({"error": str(e)}, 500)

    def _handle_geotagged_photos(self):
        try:
            log_msg("POST /geotagged_photos")
            content_type = self.headers.get("Content-Type", "")
            raw = self._read_body()

            name = "Geotagged photos"

            if "multipart/form-data" not in content_type:
                self._send_json_response(
                    {"status": "failed", "error": "Expected multipart/form-data"}, 400
                )
                return

            # Extract boundary from Content-Type header
            boundary = None
            for part in content_type.split(";"):
                part = part.strip()
                if part.startswith("boundary="):
                    boundary = part.split("=", 1)[1].strip('"')
                    break

            if not boundary:
                self._send_json_response(
                    {"status": "failed", "error": "No boundary in multipart"}, 400
                )
                return

            fields, files = _parse_multipart(raw, boundary)

            if "name" in fields:
                name = fields["name"]

            if not files:
                self._send_json_response(
                    {"status": "failed", "error": "No files uploaded"}, 400
                )
                return

            # Save uploaded files to a temporary directory
            temp_dir = tempfile.mkdtemp()
            for _, filename, data in files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(data)

            plugin = get_plugin()
            if not plugin:
                self._send_json_response({"error": "Plugin not initialized"}, 500)
                return
            result = plugin.add_geotagged_photos(temp_dir, name)
            if result:
                self._send_json_response({"status": "success"})
            else:
                self._send_json_response({"status": "failed"})
        except Exception as e:
            log_msg(f"Error in geotagged_photos endpoint: {e}")
            self._send_json_response({"status": "failed", "error": str(e)}, 500)

    def _handle_geojson(self):
        try:
            log_msg("POST /geojson")
            body = self._parse_request_body()

            name = body.get("name")
            geojson = body.get("geojson")

            log_msg(f"POST get something {name}")
            plugin = get_plugin()
            if not plugin:
                self._send_json_response({"error": "Plugin not initialized"}, 500)
                return
            result = plugin.add_geojson_layer(name, geojson)
            if result:
                self._send_json_response({"status": "success"})
            else:
                self._send_json_response({"status": "failed"})
        except Exception as e:
            log_msg(f"Error in post_geojson endpoint: {e}")
            self._send_json_response({"error": str(e)}, 500)


# ----------------------------------------------------------------------
# Server (threading-capable, reusable address)
# ----------------------------------------------------------------------

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """HTTPServer that handles each request in a new thread."""
    daemon_threads = True
    allow_reuse_address = True


# ----------------------------------------------------------------------
# Public API (same interface as the old FastAPI-based module)
# ----------------------------------------------------------------------

def start_web_server(qgis_plugin):
    global _qgis_plugin, server, _server_thread, PORT
    _qgis_plugin = qgis_plugin
    import sys
    sys.tlgeo_plugin = qgis_plugin

    log_msg("Trying to run HTTP server")

    port_ready = threading.Event()

    def run_server():
        global server, PORT
        host_bind = ".".join(["0", "0", "0", "0"])

        for port in range(BASE_PORT, BASE_PORT + MAX_PORT_RETRIES):
            try:
                server = ThreadedHTTPServer((host_bind, port), TLGeoRequestHandler)
                PORT = port
                port_ready.set()
                log_msg(f"Server started on {host_bind}:{port}")
                server.serve_forever()
                log_msg(f"Server has stopped running on port {port}")
                return
            except OSError as err:
                if "Address already in use" in str(err) or getattr(err, 'errno', None) == 48:
                    log_msg(f"Port {port} is in use, trying next...")
                    continue
                else:
                    log_msg(f"ERROR on running HTTP server: {err}")
                    port_ready.set()
                    return

        log_msg(f"ERROR: Could not find available port in range {BASE_PORT}-{BASE_PORT + MAX_PORT_RETRIES - 1}")
        port_ready.set()

    _server_thread = threading.Thread(target=run_server, daemon=True)
    _server_thread.start()

    # Wait briefly for port to be resolved so other modules can read PORT
    port_ready.wait(timeout=3)
    log_msg(f"Server port resolved: {PORT}")


def stop():
    """Stop the HTTP server gracefully (synchronous)."""
    global server
    log_msg("Trying to stop HTTP server")
    try:
        if server:
            server.shutdown()
            server.server_close()
    except Exception as e:
        log_msg(f"Could not force shutdown server: {e}")
        _ = e
    server = None
    log_msg("Server was stopped")
