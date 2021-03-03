import hashlib
import asyncio
import threading


class Server:
    def __init__(self, ip, node, port=42069) -> None:
        self.ip = ip
        self.port = port
        self.node = node
        self.hash = hashlib.sha1(("%s:%s" % (self.ip, self.port)).encode('ASCII')).hexdigest()
        self.id = int(self.hash, 16) % 5
        print('Starting to listen')
        self.listen()

    def join(self, ip, port) -> None:
        print('Join %s %s' % (ip,port))
        joinID = int(hashlib.sha1(("%s:%s" % (ip, port)).encode('ASCII')).hexdigest(), 16) % 5
        print('Join id is %s' % joinID)
        if(self.node.id < joinID < self.node.next.id or self.node.next is self.node):
            oldNextIP = self.node.next.ip
            oldNextPort = self.node.next.port
            self.node.setNext(ip,port)
            self.node.next.connection.send('next:%s,%s|' % (oldNextIP, oldNextPort))
            self.node.next.connection.send('prev:%s,%s' % (self.ip, self.port))
        else:
            self.node.next.connection.send('join:%s,%s' % (ip, port))

    def depart(self,departID) -> None:
        if( departID == self.node.id ):
            self.node.previous.connection('next:%s,%s|' % (self.node.next.ip,self.node.next.port))
            self.node.next.connection('prev:%s,%s' % (self.node.next.ip,self.node.next.port))
        else:
            self.node.next.connection('depart:%s',departID)

    def handle_request(self, requests) -> None:
        for request in requests.split('|'):
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
            data = await reader.read(255)
            message = data.decode()
            addr = writer.get_extra_info('peername')
            print("Received %r from %r" % (message, addr))
            self.handle_request(message)
            print("Send: %r" % message)
            writer.write(data)
            await writer.drain()

            print("Close the client socket")
            writer.close()


        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.start_server(handle_client, self.ip, self.port))
        loop.run_forever()
