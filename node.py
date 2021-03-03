from remote import Remote
from server import Server

import hashlib
import socket
import fcntl
import struct

masterIP = '192.168.1.5'

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])

class Node:
    def __init__(self, ip, port=42069) -> None:
        self.ip = ip
        self.port = int(port)
        self.id = int( hashlib.sha1( ("%s:%s" % (self.ip,self.port)).encode('ASCII') ).hexdigest(), 16) % 5
        self.next = self
        self.previous = self
        self.connection = None
        # if(self.ip != masterIP):
        #     self.join()
        if( self.ip == get_ip_address('eth1')):
            self.server = Server(self.ip,self)

    # def join(self):
    #     masterConnection = Remote(masterIP)
    #     masterConnection.open_connection()
    #     masterConnection.send('HELLO WORLD')

    def setNext(self, ip, port=42069) -> None:
        if( self.next is not self ):  
            self.next.connection.close_connection()
        self.next = Node(ip, port)
        self.next.connection = Remote(self.next.ip, self.next.port)
        print('Added %s as next' % ip)


    def setPrevious(self, ip, port=42069) -> None:
        self.previous = Node(ip,port)
        self.previous.connection = Remote(self.previous.ip, self.previous.port)
        print('Added %s as previous' % ip)

    def __str__(self) -> None:
        return "I'm node with ip=%s" % self.ip


if __name__ == "__main__":
    ip = get_ip_address('eth1')
    print('My ip is %s' % ip)
    node = Node(ip)