from node import Node

import socket
import hashlib
import asyncio


HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)


class Server:
    def __init__(self, ip, node: Node, port=69420) -> None:
        self.ip = ip
        self.port = port
        self.node: Node = node
        self.hash = hashlib.sha1(("%s:%s" % (self.ip, self.port)).encode('ASCII')).hexdigest()
        self.id = int(self.hash, 16)

    def join(self, ip, port) -> None:
        joinID = int(hashlib.sha1(("%s:%s" % (ip, port)).encode('ASCII')).hexdigest(), 16)
        if(self.node.id < joinID < self.node.next.id or self.node.next is self.node):
            oldNextIP = self.node.next.ip
            oldNextPort = self.node.next.port
            self.node.setNext(Node(ip, port))
            self.node.next.connection.send('next:%s,%s' % (oldNextIP, oldNextPort))
            self.node.next.connection.send('prev:%s,%s' % (self.ip, self.port))
        else:
            self.node.next.connection.send('join:%s,%s' % (ip, port))

    def depart(self,departID) -> None:
        if( departID == self.node.id ):
            self.node.previous.connection('next:%s,%s' % (self.node.next.ip,self.node.next.port))
            self.node.next.connection('prev:%s,%s' % (self.node.next.ip,self.node.next.port))
        else:
            self.node.next.connection('depart:%s',departID)

    def handle_request(self, request) -> None:
        command = request.split(':')[0]
        if(command == 'join'):
            ip = request.split(':')[1].split(',')[0]
            port = request.split(':')[1].split(',')[1]
            self.join(ip, port)
        elif(command == 'next'):
            ip = request.split(':')[1].split(',')[0]
            port = request.split(':')[1].split(',')[1]
            self.node.setNext(ip, port)
        elif(command == 'prev'):
            ip = request.split(':')[1].split(',')[0]
            port = request.split(':')[1].split(',')[1]
            self.node.setPrevious(ip, port)
        elif(command == 'depart'):
            departID = request.split(':')[1]
            self.depart(departID)

    def listen(self) -> None:
        async def handle_client(reader, writer):
            request = None
            while request != 'quit':
                request = (await reader.read(255)).decode('utf8')
                self.handle_request(request)
            writer.close()

        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.start_server(
            handle_client, self.ip, self.port))
        loop.run_forever()
