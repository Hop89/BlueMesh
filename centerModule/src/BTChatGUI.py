import asyncio
import base64
import hashlib
import json
import os
import queue
import socket
import threading
import tkinter as tk
import uuid
from tkinter import filedialog, ttk
from urllib import parse, request
import os
from dotenv import load_dotenv

load_dotenv()
WX_TOKEN = os.environ.get("WX_TOKEN")

try:
    from bleak import BleakScanner
except Exception:  # noqa: BLE001
    BleakScanner = None


def fetch_weather(city: str) -> str:
    city = city.strip() or "Boston"

    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
    )
    alert_url = "http://api.weatherapi.com/v1/alerts.json?key={WX_TOKEN}&q={city}"


    with request.urlopen(geo_url, timeout=8) as resp:
        geo = json.loads(resp.read().decode("utf-8"))

    with request.urlopen(alert_url, timeout=8) as resp:
        alerts = json.loads(resp.read().decode("utf-8"))['alerts']['alert']

    results = geo.get("results") or []
    if not results:
        return f"Weather API: could not find city '{city}'."

    first = results[0]
    lat = first["latitude"]
    lon = first["longitude"]
    resolved_name = first.get("name", city)

    wx_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + parse.urlencode({"latitude": lat, "longitude": lon, "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"})
    )
    with request.urlopen(wx_url, timeout=8) as resp:
        wx = json.loads(resp.read().decode("utf-8"))

    current = wx.get("daily", {})
    hitemp = current.get("temperature_2m_max", "?")
    lotemp = current.get("temperature_2m_min", "?")
    precipprob = current.get("precipitation_probability_max", "?")
    code = current.get("weather_code", "?")
    return f"Weather in {resolved_name}: High: {hitemp}*C, Low: {lotemp}*C, Precipitation: {precipprob}%, code {code}, ALERTS: {alert for alert in alerts})"


def fetch_web_answer(query: str) -> str:
    query = query.strip()
    if not query:
        return "Web search: enter a query first."

    search_url = (
        "https://api.duckduckgo.com/?"
        + parse.urlencode(
            {
                "q": query,
                "format": "json",
                "no_html": 1,
                "no_redirect": 1,
                "skip_disambig": 0,
            }
        )
    )
    with request.urlopen(search_url, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    abstract = (data.get("AbstractText") or "").strip()
    if abstract:
        source = data.get("AbstractSource") or "web"
        return f"{source}: {abstract}"

    related = data.get("RelatedTopics") or []
    for item in related:
        text = (item.get("Text") or "").strip() if isinstance(item, dict) else ""
        if text:
            return f"Web result: {text}"
        if isinstance(item, dict):
            nested = item.get("Topics") or []
            for n in nested:
                nested_text = (n.get("Text") or "").strip()
                if nested_text:
                    return f"Web result: {nested_text}"

    if data.get("Answer"):
        return f"Answer: {data['Answer']}"
    return "Web search: no quick answer found."


class BTChatGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BlueMesh Bluetooth Chat")

        self.mode = tk.StringVar(value="server")
        self.host = tk.StringVar(value="00:00:00:00:00:00")
        self.server = tk.StringVar(value="")
        self.port = tk.IntVar(value=4)
        self.nickname = tk.StringVar(value="pc")
        self.city = tk.StringVar(value="Boston")
        self.search_query = tk.StringVar(value="")
        self.message = tk.StringVar()
        self.node_pick = tk.StringVar(value="")
        self.discovered_nodes: list[dict[str, str]] = []

        self.sock = None
        self.conn = None
        self.running = False
        self.send_lock = threading.Lock()
        self.ui_queue: queue.Queue[str] = queue.Queue()
        self.incoming_files: dict[str, dict] = {}

        self._build_ui()
        self._poll_ui_queue()
        self._update_mode_widgets()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        mode_row = ttk.Frame(frame)
        mode_row.grid(row=0, column=0, sticky="w")
        ttk.Label(mode_row, text="Mode:").grid(row=0, column=0, padx=(0, 8))
        ttk.Radiobutton(mode_row, text="Server", value="server", variable=self.mode, command=self._update_mode_widgets).grid(
            row=0, column=1
        )
        ttk.Radiobutton(mode_row, text="Client", value="client", variable=self.mode, command=self._update_mode_widgets).grid(
            row=0, column=2
        )

        cfg = ttk.Frame(frame)
        cfg.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        cfg.columnconfigure(1, weight=1)

        ttk.Label(cfg, text="Host bind (server):").grid(row=0, column=0, sticky="w")
        self.host_entry = ttk.Entry(cfg, textvariable=self.host)
        self.host_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(cfg, text="Server MAC (client):").grid(row=1, column=0, sticky="w")
        self.server_entry = ttk.Entry(cfg, textvariable=self.server)
        self.server_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(cfg, text="Port:").grid(row=2, column=0, sticky="w")
        self.port_entry = ttk.Entry(cfg, textvariable=self.port)
        self.port_entry.grid(row=2, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(cfg, text="Nickname:").grid(row=3, column=0, sticky="w")
        self.nick_entry = ttk.Entry(cfg, textvariable=self.nickname)
        self.nick_entry.grid(row=3, column=1, sticky="ew", padx=(8, 0))

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=2, column=0, sticky="w")
        self.connect_btn = ttk.Button(btn_row, text="Connect/Start", command=self.start_connection)
        self.connect_btn.grid(row=0, column=0)
        self.disconnect_btn = ttk.Button(btn_row, text="Disconnect", command=self.stop_connection)
        self.disconnect_btn.grid(row=0, column=1, padx=(8, 0))
        self.send_file_btn = ttk.Button(btn_row, text="Send File", command=self.send_file_from_host)
        self.send_file_btn.grid(row=0, column=2, padx=(8, 0))

        self.log = tk.Text(frame, height=16, width=90, state="disabled")
        self.log.grid(row=3, column=0, sticky="nsew", pady=(8, 8))
        frame.rowconfigure(3, weight=1)

        msg_row = ttk.Frame(frame)
        msg_row.grid(row=4, column=0, sticky="ew")
        msg_row.columnconfigure(0, weight=1)
        self.msg_entry = ttk.Entry(msg_row, textvariable=self.message)
        self.msg_entry.grid(row=0, column=0, sticky="ew")
        self.msg_entry.bind("<Return>", lambda _e: self.send_message())
        ttk.Button(msg_row, text="Send", command=self.send_message).grid(row=0, column=1, padx=(8, 0))

        weather_row = ttk.Frame(frame)
        weather_row.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(weather_row, text="City:").grid(row=0, column=0)
        self.city_entry = ttk.Entry(weather_row, textvariable=self.city, width=20)
        self.city_entry.grid(row=0, column=1, padx=(6, 8))
        self.weather_btn = ttk.Button(weather_row, text="Get Weather API", command=self.request_weather)
        self.weather_btn.grid(row=0, column=2)

        search_row = ttk.Frame(frame)
        search_row.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        search_row.columnconfigure(1, weight=1)
        ttk.Label(search_row, text="Web Search:").grid(row=0, column=0, sticky="w")
        self.search_entry = ttk.Entry(search_row, textvariable=self.search_query)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(6, 8))
        self.search_entry.bind("<Return>", lambda _e: self.request_web_search())
        self.search_btn = ttk.Button(search_row, text="Search Web API", command=self.request_web_search)
        self.search_btn.grid(row=0, column=2)

        nodes_row = ttk.Frame(frame)
        nodes_row.grid(row=7, column=0, sticky="ew", pady=(8, 0))
        nodes_row.columnconfigure(1, weight=1)
        ttk.Label(nodes_row, text="BlueCast/BlueMesh nodes:").grid(row=0, column=0, sticky="w")
        self.nodes_combo = ttk.Combobox(nodes_row, textvariable=self.node_pick, state="readonly")
        self.nodes_combo.grid(row=0, column=1, sticky="ew", padx=(6, 8))
        self.nodes_combo.bind("<<ComboboxSelected>>", lambda _e: self.select_discovered_node())
        self.scan_btn = ttk.Button(nodes_row, text="Scan Nodes", command=self.scan_nodes)
        self.scan_btn.grid(row=0, column=2)

    def _update_mode_widgets(self):
        is_server = self.mode.get() == "server"
        self.host_entry.configure(state="normal" if is_server else "disabled")
        self.server_entry.configure(state="disabled" if is_server else "normal")
        self.weather_btn.configure(state="normal" if not is_server else "disabled")
        self.search_btn.configure(state="normal" if not is_server else "disabled")
        self.search_entry.configure(state="normal" if not is_server else "disabled")
        self.scan_btn.configure(state="normal" if not is_server else "disabled")
        self.nodes_combo.configure(state="readonly" if not is_server else "disabled")
        self.send_file_btn.configure(state="normal" if is_server else "disabled")

    def _append_log(self, text: str):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll_ui_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                self._append_log(msg)
        except queue.Empty:
            pass
        self.root.after(120, self._poll_ui_queue)

    def _log(self, text: str):
        self.ui_queue.put(text)

    def start_connection(self):
        if self.running:
            self._log("[system] already running")
            return
        self.running = True

        if self.mode.get() == "server":
            t = threading.Thread(target=self._server_thread, daemon=True)
        else:
            t = threading.Thread(target=self._client_thread, daemon=True)
        t.start()

    def stop_connection(self):
        self.running = False
        try:
            if self.conn:
                self.conn.close()
        except OSError:
            pass
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass
        self.conn = None
        self.sock = None
        self._log("[system] disconnected")

    def _recv_loop(self, conn: socket.socket):
        rx_buffer = b""
        while self.running:
            try:
                data = conn.recv(1024)
                if not data:
                    self._log("[system] peer disconnected")
                    break
                rx_buffer += data
                while b"\n" in rx_buffer:
                    raw_line, rx_buffer = rx_buffer.split(b"\n", 1)
                    text = raw_line.decode("utf-8", errors="replace").strip()
                    if not text:
                        continue
                    if not self._handle_protocol_message(text):
                        self._log(f"peer: {text}")
            except OSError as exc:
                self._log(f"[system] receive error: {exc}")
                break
        self.running = False

    def _send_line(self, text: str) -> bool:
        if not self.running or not self.conn:
            self._log("[system] not connected")
            return False
        try:
            payload = (text + "\n").encode("utf-8")
            with self.send_lock:
                self.conn.sendall(payload)
            return True
        except OSError as exc:
            self._log(f"[system] send error: {exc}")
            return False

    def _handle_protocol_message(self, text: str) -> bool:
        if self._handle_file_protocol(text):
            return True
        return self._handle_host_command(text)

    def _handle_host_command(self, text: str) -> bool:
        if self.mode.get() != "server":
            return False

        msg = text.strip()
        if msg.startswith("/weather "):
            city = msg[len("/weather ") :].strip() or "Boston"

            def worker():
                try:
                    self._log(f"[host] weather request: {city}")
                    result = fetch_weather(city)
                    self._send_line(f"[weather] {result}")
                    self._log(f"[host->peer] [weather] {result}")
                except Exception as exc:  # noqa: BLE001
                    err = f"[weather] request failed: {exc}"
                    self._send_line(err)
                    self._log(f"[host->peer] {err}")

            threading.Thread(target=worker, daemon=True).start()
            return True

        if msg.startswith("/search "):
            query = msg[len("/search ") :].strip()

            def worker():
                try:
                    self._log(f"[host] search request: {query or '<empty>'}")
                    result = fetch_web_answer(query)
                    self._send_line(f"[search] {result}")
                    self._log(f"[host->peer] [search] {result}")
                except Exception as exc:  # noqa: BLE001
                    err = f"[search] request failed: {exc}"
                    self._send_line(err)
                    self._log(f"[host->peer] {err}")

            threading.Thread(target=worker, daemon=True).start()
            return True

        return False

    def _handle_file_protocol(self, text: str) -> bool:
        if not text.startswith("/file_"):
            return False

        parts = text.split(" ", 3)
        cmd = parts[0]

        if cmd == "/file_begin":
            if len(parts) < 4:
                self._log("[file] malformed /file_begin")
                return True
            transfer_id = parts[1]
            name = parse.unquote(parts[2])
            try:
                expected_size = int(parts[3])
            except ValueError:
                self._log("[file] invalid size in /file_begin")
                return True
            self.incoming_files[transfer_id] = {
                "name": name,
                "size": expected_size,
                "buf": bytearray(),
                "sha": hashlib.sha256(),
            }
            self._log(f"[file] incoming '{name}' ({expected_size} bytes)")
            return True

        if cmd == "/file_chunk":
            if len(parts) < 4:
                self._log("[file] malformed /file_chunk")
                return True
            transfer_id = parts[1]
            state = self.incoming_files.get(transfer_id)
            if state is None:
                self._log("[file] chunk for unknown transfer")
                return True
            chunk_parts = parts[3].split(" ", 1)
            if len(chunk_parts) != 2:
                self._log("[file] malformed chunk payload")
                return True
            b64_data = chunk_parts[1]
            try:
                data = base64.b64decode(b64_data)
            except Exception:  # noqa: BLE001
                self._log("[file] invalid base64 chunk")
                return True
            state["buf"].extend(data)
            state["sha"].update(data)
            return True

        if cmd == "/file_end":
            if len(parts) < 4:
                self._log("[file] malformed /file_end")
                return True
            transfer_id = parts[1]
            end_parts = parts[3].split(" ", 1)
            if len(end_parts) != 2:
                self._log("[file] malformed /file_end payload")
                return True

            state = self.incoming_files.pop(transfer_id, None)
            if state is None:
                self._log("[file] end for unknown transfer")
                return True

            expected_sha = end_parts[1].strip()
            actual_sha = state["sha"].hexdigest()
            if actual_sha != expected_sha:
                self._log("[file] checksum mismatch; file discarded")
                return True

            inbox_dir = os.path.join(os.path.expanduser("~"), "Downloads", "BlueMeshInbox")
            os.makedirs(inbox_dir, exist_ok=True)
            safe_name = self._safe_filename(state["name"])
            out_path = os.path.join(inbox_dir, safe_name)
            base, ext = os.path.splitext(out_path)
            suffix = 1
            while os.path.exists(out_path):
                out_path = f"{base}_{suffix}{ext}"
                suffix += 1

            with open(out_path, "wb") as f:
                f.write(state["buf"])

            size = len(state["buf"])
            self._log(f"[file] saved {size} bytes to {out_path}")
            return True

        return False

    def _safe_filename(self, name: str) -> str:
        cleaned = "".join(ch for ch in name if ch not in '<>:"/\\|?*').strip()
        return cleaned or "received_file.bin"

    def _server_thread(self):
        try:
            self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.sock.bind((self.host.get().strip(), int(self.port.get())))
            self.sock.listen(1)
            bound_host, bound_port = self.sock.getsockname()
            self._log(f"[system] server waiting on {bound_host}:{bound_port}")
            self.conn, addr = self.sock.accept()
            self._log(f"[system] connected: {addr}")
            self._recv_loop(self.conn)
        except OSError as exc:
            self._log(f"[system] server error: {exc}")
            self.running = False

    def _client_thread(self):
        try:
            self.conn = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.conn.connect((self.server.get().strip(), int(self.port.get())))
            self._log(f"[system] connected to {self.server.get().strip()}:{int(self.port.get())}")
            self._recv_loop(self.conn)
        except OSError as exc:
            self._log(f"[system] client error: {exc}")
            self.running = False

    def send_message(self):
        text = self.message.get().strip()
        if not text:
            return
        payload = f"{self.nickname.get().strip() or 'pc'}: {text}"
        if self._send_line(payload):
            self._log(f"me: {text}")
            self.message.set("")

    def send_file_from_host(self):
        if self.mode.get() != "server":
            self._log("[file] only host/server can send files.")
            return
        if not self.running or not self.conn:
            self._log("[file] connect first.")
            return
        file_path = filedialog.askopenfilename(title="Select file to send")
        if not file_path:
            return
        threading.Thread(target=self._send_file_worker, args=(file_path,), daemon=True).start()

    def _send_file_worker(self, file_path: str):
        try:
            filename = os.path.basename(file_path)
            size = os.path.getsize(file_path)
            transfer_id = uuid.uuid4().hex[:10]
            encoded_name = parse.quote(filename, safe="")
            sha = hashlib.sha256()

            self._log(f"[file] sending '{filename}' ({size} bytes)")
            if not self._send_line(f"/file_begin {transfer_id} {encoded_name} {size}"):
                return

            chunk_size = 700
            chunk_count = 0
            sent_bytes = 0
            with open(file_path, "rb") as f:
                while True:
                    block = f.read(chunk_size)
                    if not block:
                        break
                    sha.update(block)
                    b64 = base64.b64encode(block).decode("ascii")
                    if not self._send_line(f"/file_chunk {transfer_id} {chunk_count} {b64}"):
                        return
                    chunk_count += 1
                    sent_bytes += len(block)
                    if chunk_count % 50 == 0 or sent_bytes == size:
                        self._log(f"[file] progress {sent_bytes}/{size} bytes")

            digest = sha.hexdigest()
            self._send_line(f"/file_end {transfer_id} {chunk_count} {digest}")
            self._log(f"[file] sent '{filename}' ({size} bytes, {chunk_count} chunks)")
        except Exception as exc:  # noqa: BLE001
            self._log(f"[file] send failed: {exc}")

    def request_weather(self):
        city = self.city.get().strip() or "Boston"
        if self.mode.get() == "client":
            if self._send_line(f"/weather {city}"):
                self._log(f"[client] weather request sent to host: {city}")
            return

        def worker():
            try:
                self._log("[weather] requesting weather API...")
                result = fetch_weather(city)
                self._log(f"[weather] {result}")
                self._send_line(f"[weather] {result}")
            except Exception as exc:  # noqa: BLE001
                self._log(f"[weather] request failed: {exc}")

        threading.Thread(target=worker, daemon=True).start()

    def request_web_search(self):
        q = self.search_query.get().strip()
        if self.mode.get() == "client":
            if self._send_line(f"/search {q}"):
                self._log(f"[client] search request sent to host: {q or '<empty>'}")
            return

        def worker():
            try:
                self._log(f"[search] querying: {q or '<empty>'}")
                result = fetch_web_answer(q)
                self._log(f"[search] {result}")
                self._send_line(f"[search] {result}")
            except Exception as exc:  # noqa: BLE001
                self._log(f"[search] request failed: {exc}")

        threading.Thread(target=worker, daemon=True).start()

    def scan_nodes(self):
        def worker():
            if BleakScanner is None:
                self._log("[scan] bleak not installed. Run: pip install bleak")
                return
            try:
                self._log("[scan] scanning for BLE advertisements (6s)...")
                devices = asyncio.run(BleakScanner.discover(timeout=6.0))
                filtered = []
                for d in devices:
                    name = (d.name or "").strip()
                    address = (getattr(d, "address", "") or "").strip()
                    if not address:
                        continue
                    if "bluecast" in name.lower() or "bluemesh" in name.lower():
                        filtered.append({"name": name or "Unknown", "address": address})

                self.discovered_nodes = filtered
                if not filtered:
                    self.root.after(
                        0,
                        lambda: (
                            self.nodes_combo.configure(values=[]),
                            self.node_pick.set(""),
                        ),
                    )
                    self._log("[scan] no BlueCast/BlueMesh nodes found.")
                    return

                labels = [f"{n['name']} ({n['address']})" for n in filtered]
                self.root.after(
                    0,
                    lambda: (
                        self.nodes_combo.configure(values=labels),
                        self.node_pick.set(labels[0]),
                        self.select_discovered_node(),
                    ),
                )
                self._log(f"[scan] found {len(filtered)} node(s).")
            except Exception as exc:  # noqa: BLE001
                self._log(f"[scan] failed: {exc}")

        threading.Thread(target=worker, daemon=True).start()

    def select_discovered_node(self):
        selection = self.node_pick.get().strip()
        if not selection:
            return
        start = selection.rfind("(")
        end = selection.rfind(")")
        if start == -1 or end == -1 or end <= start + 1:
            return
        addr = selection[start + 1 : end].strip()
        if addr:
            self.server.set(addr)
            self._log(f"[scan] selected node {addr}")


def main():
    root = tk.Tk()
    app = BTChatGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_connection(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
