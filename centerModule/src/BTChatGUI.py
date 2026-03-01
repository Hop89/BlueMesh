import json
import queue
import socket
import threading
import tkinter as tk
from tkinter import ttk
from urllib import parse, request


def fetch_weather(city: str) -> str:
    city = city.strip() or "Boston"

    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
    )
    with request.urlopen(geo_url, timeout=8) as resp:
        geo = json.loads(resp.read().decode("utf-8"))

    results = geo.get("results") or []
    if not results:
        return f"Weather API: could not find city '{city}'."

    first = results[0]
    lat = first["latitude"]
    lon = first["longitude"]
    resolved_name = first.get("name", city)

    wx_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + parse.urlencode({"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code"})
    )
    with request.urlopen(wx_url, timeout=8) as resp:
        wx = json.loads(resp.read().decode("utf-8"))

    current = wx.get("current", {})
    temp = current.get("temperature_2m", "?")
    code = current.get("weather_code", "?")
    return f"Weather in {resolved_name}: {temp}C (code {code})"


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
        self.message = tk.StringVar()

        self.sock = None
        self.conn = None
        self.running = False
        self.ui_queue: queue.Queue[str] = queue.Queue()

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

    def _update_mode_widgets(self):
        is_server = self.mode.get() == "server"
        self.host_entry.configure(state="normal" if is_server else "disabled")
        self.server_entry.configure(state="disabled" if is_server else "normal")
        # Weather button is intended for client workflow.
        self.weather_btn.configure(state="normal" if not is_server else "disabled")

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
        while self.running:
            try:
                data = conn.recv(1024)
                if not data:
                    self._log("[system] peer disconnected")
                    break
                self._log(f"peer: {data.decode('utf-8', errors='replace')}")
            except OSError as exc:
                self._log(f"[system] receive error: {exc}")
                break
        self.running = False

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
        if not self.running or not self.conn:
            self._log("[system] not connected")
            return
        text = self.message.get().strip()
        if not text:
            return
        payload = f"{self.nickname.get().strip() or 'pc'}: {text}".encode("utf-8")
        try:
            self.conn.send(payload)
            self._log(f"me: {text}")
            self.message.set("")
        except OSError as exc:
            self._log(f"[system] send error: {exc}")

    def request_weather(self):
        def worker():
            try:
                self._log("[weather] requesting weather API...")
                result = fetch_weather(self.city.get())
                self._log(f"[weather] {result}")
            except Exception as exc:  # noqa: BLE001
                self._log(f"[weather] request failed: {exc}")

        threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    app = BTChatGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_connection(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()