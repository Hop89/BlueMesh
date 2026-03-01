import socket

server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
server.bind(("70:9C:D1:B5:BB:7E", 4))
server.listen(1)

client, addr = server.accept()

try:
    while True:
        data = client.recv(1024)
        if not data:
            break
        print(data.decode('utf-8'))
        client.send("test".encode('utf-8'))
except OSError as e:
    pass

client.close()
server.close()

