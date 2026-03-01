import socket

client = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
client.connect(("70:9C:D1:B5:BB:7E", 4))

try:
    while True:
        client.send("test from other computer".encode("utf-8"))
        data = client.recv(1024)
        if not data:
            break
        print(data.decode('utf-8'))
except OSError as e:
    pass

client.close()