#!/usr/bin/env python3

import socket

class Remote:
    def __init__(self, ip, port=42069) -> None:
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip,port))

    def close_connection(self) -> None:
        self.socket.close()

    def send(self, msg) -> None:
        self.socket.sendall(msg.encode())

    def receive(self) -> None:
        print('Received %s' % self.socket.recv(255).decode())
