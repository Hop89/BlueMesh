import argparse
import socket
import threading
# Computer A commands
# cd centerModule
# python src\BTServer.py --host 00:00:00:00:00:00 --port 4 --nickname pc-a

# Computer B commands 
# python src\BTClient.py --server <PC_A_BLUETOOTH_MAC> --port 4 --nickname pc-b


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
    parser = argparse.ArgumentParser(description="Bluetooth RFCOMM chat client (computer-to-computer)")
    parser.add_argument("--server", required=True, help="Server computer Bluetooth MAC address")
    parser.add_argument("--port", type=int, default=4, help="RFCOMM channel/port")
    parser.add_argument("--nickname", default="client")
    return parser.parse_args()


def main():
    args = parse_args()

    conn = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    try:
        conn.connect((args.server, args.port))
    except OSError as exc:
        print(f"[system] connect failed: {exc}")
        return

    print(f"[system] connected to {args.server}:{args.port}")
    print("[system] type messages, /quit to exit")

    t = threading.Thread(target=recv_loop, args=(conn,), daemon=True)
    t.start()

    send_loop(conn, args.nickname)


if __name__ == "__main__":
    main()