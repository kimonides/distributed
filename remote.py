#!/usr/bin/env python3

import socket
import hashlib


class Remote:
    def __init__(self, ip, port=69420) -> None:
        self.ip = ip
        self.port = port

    def open_connection(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))

    def close_connection(self) -> None:
        self.socket.close()
        self.socket = None

    def send(self, msg) -> None:
        self.socket.sendall(msg + "\r\n")
