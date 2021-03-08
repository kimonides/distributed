from remote import Remote
from server import Server

import hashlib
import socket
import fcntl
import struct
from uuid import uuid4

masterIP = '192.168.1.5'
masterPort = 42096
ringSize = 10


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
        self.id = self.hash('%s:%s' % (self.ip,self.port))
        self.next = self
        self.previous = self
        self.connection = None
        self.data = {}
        # if(self.ip != masterIP):
        #     self.joinRing()
        if(self.ip == get_ip_address('eth1')):
            self.server = Server(self.ip, self)

    def joinRing(self) -> None:
        msg = 'join:%s,%s\n%s\n%s' % (self.ip, self.port,masterIP, masterPort)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('(%s,%s)' % (masterIP,masterPort))
        s.connect((masterIP,masterPort))
        s.sendall(msg.encode())
        s.close()
        print('Received %s' % s.recv(1023).decode())
        print('Joined ring')
        s.close()

    def sendToNext(self,request):
        requestID = None
        if(len(request.split('\n'))<4):
            requestID = uuid4()
            request+='\n%s' % requestID
        print('Sending %s to %s' % (repr(request),self.next.ip))
        self.next.connection.send(request)
        return requestID

    def sendToPrevious(self,request):
        requestID = None
        if(len(request.split('\n'))<4):
            requestID = uuid4()
            request+='\n%s' % requestID
        print('Sending %s to %s' % (repr(request),self.previous.ip))
        self.previous.connection.send(request)
        return requestID
    
    def parseRequest(self,request):
        rv = {}
        rv['responseNodeIP'] = request.split('\n')[1]
        rv['responseNodePort'] = request.split('\n')[2]
        try:
            rv['requestID'] = request.split('\n')[3]
        except:
            pass
        rv['command'] = request.split(':')[0]
        if(rv['command'] == 'insert'):
            rv['key'] = int(request.split('\n')[0].split(':')[1].split(',')[0])
            rv['value'] = request.split('\n')[0].split(':')[1].split(',')[1]
        elif(rv['command'] == 'join'):
            rv['ip'] = request.split('\n')[0].split(':')[1].split(',')[0]
            rv['port'] = request.split('\n')[0].split(':')[1].split(',')[1]
        elif(rv['command'] == 'depart'):
            rv['id'] = int(request.split('\n')[0].split(':')[1])
        elif(rv['command'] == 'delete' or rv['command'] == 'query'):
            rv['key'] = int(request.split('\n')[0].split(':')[1].split(',')[0])
            if(rv['key'] == '*'):
                rv['running_response'] = request.split('\n')[0].split(':')[1].split(',')[1]
        return rv

    def sendResponse(self,request,response):
        responseNodeIP = request.split('\n')[1]
        responseNodePort = int(request.split('\n')[2])
        if(self.ip == responseNodeIP and self.port == responseNodePort):
            return response
        try:
            requestID = request.split('\n')[3]
        except:
            return None
        conn = Remote(responseNodeIP,responseNodePort)
        conn.send('response:%s,%s' % (requestID,response))
        return None

    def hash(self,key):
        return int(hashlib.sha1((key).encode()).hexdigest(), 16) % ringSize

    def redistribute(self,request) -> None:
        key_hash = int(request.split(':')[1].split(',')[0])
        value = request.split(':')[1].split(',')[1]
        self.data[key_hash] = value

    def insert(self, request):
        requestData = self.parseRequest(request)
        if(self.isResponsible(requestData['key'])):
            self.data[requestData['key']] = requestData['value']
            print("I'm responsible for insert with hash key %s and value %s" % (requestData['key'],requestData['value']))
            return self.sendResponse(request,'OK')
        else:
            print("I'm not responsible for id %s send to previous with ip %s" % (requestData['key'],self.previous.ip))
            return self.sendToPrevious(request)

    def delete(self,request):
        requestData = self.parseRequest(request)
        if(self.isResponsible(requestData['key'])):
            self.data.pop(requestData['key'])
            return self.sendResponse(request,'OK')
        else:
            return self.sendToNext(request)

    def isResponsible(self, hash) -> bool:
        rv = False
        if(self.next is self):
            return True
        if(self.id < self.previous.id):
            if(0 <= hash <= self.id or self.previous.id < hash < ringSize):
                rv = True
        else:
            if(self.previous.id < hash <= self.id):
                rv = True
        return rv

    def redistributeData(self, targetNode, force=False) -> None:
        print('Redistributing data to %s with id %s' % (targetNode.ip,targetNode.id))
        for key in list(self.data):
            if(not self.isResponsible(key) or force == True):
                value = self.data.pop(key)
                print('Sending key hash %s' % (key))
                targetNode.connection.send('redistribute:%s,%s' % (key, value))

    def depart(self, request):
        requestData = self.parseRequest(request)
        if(requestData['id'] == self.id):
            self.previous.connection.send('next:%s,%s|' % (self.next.ip, self.next.port))
            self.next.connection.send('prev:%s,%s|' % (self.previous.ip, self.previous.port))
            self.redistributeData(self.next,force=True)
            return self.sendResponse(request,'OK')
        else:
            return self.sendToNext(request)



    def query(self,request):
        requestData = self.parseRequest(request)
        # if(requestData['key']=='*'):
        #     myData = ''
        #     for key in self.data:
        #         myData += '?' + self.data[key]
        #     request = request.split('\n')[0]+ myData + '\n' + '\n'.join(request.split('\n')[1:])
        #     #TODO fix someway for query * to work
        #     if( requestData[''] )
        #     return self.sendToNext(request)

        if(self.isResponsible(requestData['key'])):
            if requestData['key'] in self.data:
                resp = 'Query result is %s from %s with id %s' % (self.data[requestData['key']],self.ip,self.id)
                return self.sendResponse(request,resp)
            else:
                return self.sendResponse(request,"Key hash %s doesn't exist in the DHT" % requestData['key'])
        else:
            return self.sendToNext(request)

    def join(self, request):
        requestData = self.parseRequest(request)
        ip = requestData['ip']
        port = requestData['port']
        joinID = self.hash('%s:%s' % (ip,port))
        if(self.previous.id < joinID < self.id or self.previous is self):
            oldPrevIP = self.previous.ip
            oldPrevPort = self.previous.port
            if(self.previous is self):
                self.setNext(ip, port)
            else:
                self.previous.connection.send('next:%s,%s' % (ip, port))
            self.setPrevious(ip, port)
            self.previous.connection.send('prev:%s,%s|' % (oldPrevIP, oldPrevPort))
            self.previous.connection.send('next:%s,%s' % (self.ip, self.port))
            self.redistributeData(self.previous)
            return self.sendResponse(request,'OK')
        else:
            return self.sendToNext(request)

    def setNext(self, ip, port=42069) -> None:
        if(ip==self.ip and int(port)==self.port):
            self.next = self
        else:
            self.next = Node(ip, port)
            self.next.connection = Remote(self.next.ip, self.next.port)
        print('Added %s as next' % ip)

    def setPrevious(self, ip, port=42069) -> None:
        if(ip==self.ip and int(port)==self.port):
            self.previous = self
        else:
            self.previous = Node(ip, port)
            self.previous.connection = Remote(self.previous.ip, self.previous.port)
        print('Added %s as previous' % ip)

    def __str__(self) -> None:
        return "(%s,%s,%s)-->" % (self.ip, self.port, self.id)

    def ping(self,request) -> None:
        if(self.next.ip == masterIP):
            response = request.split('\n')[0].split(":")[1] + str(self).split('-->')[0]
            return self.sendResponse(request,response)
        else:
            request = request.split('\n')[0]+str(self) + '\n' + '\n'.join(request.split('\n')[1:])
            return self.sendToNext(request)


if __name__ == "__main__":
    ip = get_ip_address('eth1')
    print('My ip is %s' % ip)
    node = Node(ip)

