#!/usr/bin/env python3

import socket

class Remote:
    def __init__(self, ip, port=42069) -> None:
        self.ip = ip
        self.port = port
        
    def send(self, msg) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip,self.port))
        s.sendall(msg.encode())
        s.close()
