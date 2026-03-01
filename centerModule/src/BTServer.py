import argparse
import socket
import threading


def recv_loop(conn: socket.socket):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print("\n[system] peer disconnected")
                break
            print(f"\npeer: {data.decode('utf-8', errors='replace')}")
    except OSError as exc:
        print(f"\n[system] receive error: {exc}")


def send_loop(conn: socket.socket, nickname: str):
    try:
        while True:
            text = input("")
            if text.strip().lower() in {"/quit", "/exit"}:
                break
            conn.send(f"{nickname}: {text}".encode("utf-8"))
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Bluetooth RFCOMM chat server (computer-to-computer)")
    parser.add_argument(
        "--host",
        default="00:00:00:00:00:00",
        help="Local Bluetooth adapter address. Use 00:00:00:00:00:00 for any adapter.",
    )
    parser.add_argument("--port", type=int, default=4, help="RFCOMM channel/port")
    parser.add_argument("--nickname", default="server")
    return parser.parse_args()


def main():
    args = parse_args()

    server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    try:
        server.bind((args.host, args.port))
    except OSError as exc:
        print(f"[system] bind failed: {exc}")
        print("[system] try --host with your Bluetooth adapter MAC")
        return

    server.listen(1)
    bound_host, bound_port = server.getsockname()
    print(f"[system] waiting on {bound_host}:{bound_port}")

    conn, addr = server.accept()
    print(f"[system] connected: {addr}")
    print("[system] type messages, /quit to exit")

    t = threading.Thread(target=recv_loop, args=(conn,), daemon=True)
    t.start()

    send_loop(conn, args.nickname)
    server.close()


if __name__ == "__main__":
    main()
