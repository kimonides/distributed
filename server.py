import hashlib
import asyncio
import threading
from uuid import uuid4
from uuid import UUID

ringSize = 10


class Server:
    def __init__(self, ip, node, port=42069) -> None:
        self.ip = ip
        self.port = port
        self.node = node
        self.hash = hashlib.sha1(("%s:%s" % (self.ip, self.port)).encode('ASCII')).hexdigest()
        self.id = int(self.hash, 16) % ringSize
        self.requestsTable = {}
        self.event = asyncio.Event()
        self.event.clear()
        self.condition = asyncio.Condition()
        #ssh -i ~/.ssh/okeanos user@83.212.74.32
        print('%s with id %s starting to listen' % (self.ip,self.id))
        self.listen()

    def isResponseNode(self,request):
        return request.split('\n')[1] == self.ip and request.split('\n')[2] == self.port

    def handle_request(self, requests):
        response = None
        for request in requests.split('|'):
            command = request.split(':')[0]
            if(command == 'next'):
                self.node.setNext(request.split(':')[1].split(',')[0],request.split(':')[1].split(',')[1])
            elif(command == 'prev'):
                self.node.setPrevious(request.split(':')[1].split(',')[0],request.split(':')[1].split(',')[1])
            if(command == 'redistribute'):
                self.node.redistribute(request)
            else:
                if(command == 'join'):
                    response = self.node.join(request)
                elif(command == 'depart'):
                    response = self.node.depart(request)
                elif(command == 'insert'):
                    response = self.node.insert(request)
                elif(command == 'ping'):
                    response = self.node.ping(request)
                elif(command == 'delete'):
                    response = self.node.delete(request)
                elif(command == 'query'):
                    response = self.node.query(request)
                elif(request.split(':')[0] == 'response'):
                    self.requestsTable[request.split(':')[1].split(',')[0]] = ','.join(request.split(':')[1].split(',')[1:])
                    self.event.set()
                    self.event.clear()
        return response


    def listen(self) -> None:
        async def handle_client(reader, writer):
            data = await reader.read(255)
            message = data.decode()
            addr = writer.get_extra_info('peername')
            print("Received %r from %r" % (message, addr))
            response = self.handle_request(message)
            if(isinstance(response,UUID)):
                print('Waiting for response for request id %s' % response)
                while True:
                    await self.event.wait()
                    if str(response) in self.requestsTable:
                        response = self.requestsTable.pop(str(response))
                        writer.write(response.encode())
                        break
            elif(response is not None):
                writer.write(response.encode())
            await writer.drain()
            writer.close()


        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.start_server(handle_client, self.ip, self.port))
        loop.run_forever()


#   responses
#   response: requestID,result
#
#   requests
#   insert:key,value\nResponseNodeIP\nResponseNodePort\nrequestID
#   