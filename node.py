from remote import Remote
from server import Server
from node import Node

import hashlib

import socket

SIZE = 16

class Node:
    def __init__(self, ip, port=69420) -> None:
        self.ip = ip
        self.server = Server(self.ip)
        self.port = port
        self.id = int( hashlib.sha1( ("%s:%s" % (self.ip,self.port)).encode('ASCII') ).hexdigest(), 16) % SIZE
        self.next: Node = self
        self.previous: Node = self
        self.connection: Remote = None

    def setNext(self,node: Node) -> None:
        if( self.next is not self ):  
            self.next.connection.close_connection()
        self.next = node
        self.next.connection = Remote(self.next.ip, self.next.port)
        self.next.connection.open_connection()


    def setPrevious(self,node: Node) -> None:
        self.previous = node
        self.previous.connection = Remote(self.previous.ip, self.previous.port)
        self.previous.connection.open_connection()





