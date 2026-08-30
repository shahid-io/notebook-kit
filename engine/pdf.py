#!/usr/bin/env python3
"""Print a local HTML file to PDF through Chrome's DevTools Protocol.

Chrome's `--print-to-pdf` CLI flag cannot template the running header and
footer, so this drives `Page.printToPDF` directly over a raw WebSocket. No
third-party packages: the handshake and frame codec below are the minimum
needed to talk to Chrome on localhost.

    python3 pdf.py in.html out.pdf '<header html>' '<footer html>' \
                   [landscape] [marginTopIn] [marginBottomIn] \
                   [paperWidthIn] [paperHeightIn]

Paper dimensions are given PORTRAIT; the landscape flag rotates them.

Falls back to `--print-to-pdf` (no page numbers) if the CDP path fails.
"""
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.request

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


# --- minimal WebSocket client -------------------------------------------------

class WS:
    def __init__(self, url):
        _, rest = url.split("://", 1)
        hostport, path = rest.split("/", 1)
        host, port = hostport.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.sock.recv(4096)
        if b"101" not in buf.split(b"\r\n", 1)[0]:
            raise RuntimeError("websocket upgrade refused")
        self.buf = buf.split(b"\r\n\r\n", 1)[1]

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise RuntimeError("socket closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, text):
        payload = text.encode()
        header = bytearray([0x81])              # FIN + text frame
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < (1 << 16):
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        mask = os.urandom(4)                    # clients must mask
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def recv(self):
        """Return one complete message, reassembling continuation frames."""
        chunks = []
        while True:
            b0, b1 = self._read(2)
            fin, opcode = b0 & 0x80, b0 & 0x0F
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            data = self._read(n) if n else b""
            if opcode == 0x8:                   # close
                raise RuntimeError("websocket closed by peer")
            if opcode == 0x9:                   # ping -> pong
                continue
            chunks.append(data)
            if fin:
                return b"".join(chunks).decode()

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


# --- CDP session --------------------------------------------------------------

def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def print_pdf(html_path, out_path, header, footer, landscape,
              margin_top, margin_bottom, paper_w=8.27, paper_h=11.69):
    port = free_port()
    proc = subprocess.Popen(
        [CHROME, "--headless=new", f"--remote-debugging-port={port}",
         "--disable-gpu", "--no-first-run", "--no-default-browser-check",
         "--user-data-dir=" + f"/tmp/cdp-{port}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(100):                    # chrome needs a moment to listen
            try:
                with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/json/version", timeout=1) as r:
                    ws_url = json.load(r)["webSocketDebuggerUrl"]
                break
            except Exception:
                time.sleep(0.1)
        if not ws_url:
            raise RuntimeError("chrome devtools never came up")

        ws = WS(ws_url)
        msg_id = [0]

        def call(method, params=None, session=None):
            msg_id[0] += 1
            req = {"id": msg_id[0], "method": method, "params": params or {}}
            if session:
                req["sessionId"] = session
            ws.send(json.dumps(req))
            while True:
                res = json.loads(ws.recv())
                if res.get("id") == msg_id[0]:
                    if "error" in res:
                        raise RuntimeError(res["error"])
                    return res.get("result", {})

        target = call("Target.createTarget", {"url": "about:blank"})["targetId"]
        session = call("Target.attachToTarget",
                       {"targetId": target, "flatten": True})["sessionId"]
        call("Page.enable", {}, session)
        call("Page.navigate", {"url": "file://" + os.path.abspath(html_path)},
             session)

        # Wait for load, ignoring the event stream's other traffic.
        deadline = time.time() + 60
        while time.time() < deadline:
            evt = json.loads(ws.recv())
            if evt.get("method") == "Page.lifecycleEvent" and \
                    evt.get("params", {}).get("name") == "networkIdle":
                break
            if evt.get("method") == "Page.loadEventFired":
                break
        time.sleep(1.2)                         # let webfonts settle

        result = call("Page.printToPDF", {
            "landscape": landscape,
            "printBackground": True,
            "preferCSSPageSize": False,
            # Portrait dimensions always: the landscape flag rotates them,
            # so swapping these too would cancel the rotation out. A4 by
            # default; the tablet edition passes 6.576 x 11.69, which rotates
            # to 11.69 x 6.576, exactly 16:9 for a landscape tablet screen.
            "paperWidth": paper_w,
            "paperHeight": paper_h,
            "marginTop": margin_top,
            "marginBottom": margin_bottom,
            "marginLeft": 0,
            "marginRight": 0,
            "displayHeaderFooter": bool(header or footer),
            "headerTemplate": header or "<span></span>",
            "footerTemplate": footer or "<span></span>",
        }, session)
        with open(out_path, "wb") as fh:
            fh.write(base64.b64decode(result["data"]))
        ws.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def fallback(html_path, out_path, landscape):
    """No running header or footer, but always works."""
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={os.path.abspath(out_path)}",
         "file://" + os.path.abspath(html_path)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    hdr = sys.argv[3] if len(sys.argv) > 3 else ""
    ftr = sys.argv[4] if len(sys.argv) > 4 else ""
    land = (len(sys.argv) > 5 and sys.argv[5] == "landscape")
    mt = float(sys.argv[6]) if len(sys.argv) > 6 else 0.55
    mb = float(sys.argv[7]) if len(sys.argv) > 7 else 0.55
    pw = float(sys.argv[8]) if len(sys.argv) > 8 else 8.27
    ph = float(sys.argv[9]) if len(sys.argv) > 9 else 11.69
    try:
        print_pdf(src, dst, hdr, ftr, land, mt, mb, pw, ph)
    except Exception as exc:                    # noqa: BLE001
        print(f"    cdp failed ({exc}); using --print-to-pdf", file=sys.stderr)
        fallback(src, dst, land)
