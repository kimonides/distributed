from remote import Remote
from server import Server

import hashlib
import socket
import fcntl
import struct
from uuid import uuid4

masterIP = '192.168.1.5'
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

    def sendToNext(self,request):
        requestID = None
        if(len(request.split('\n'))<4):
            requestID = uuid4()
            request+='\n%s' % requestID
        print('Sending %s to %s' % (request,self.next.ip))
        self.next.connection.send(request)
        return requestID

    def sendToPrevious(self,request):
        requestID = None
        if(len(request.split('\n'))<4):
            requestID = uuid4()
            request+='\n%s' % requestID
        print('Sending %s to %s' % (request,self.next.ip))
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
            rv['key'] = request.split('\n')[0].split(':')[1].split(',')[0]
            rv['value'] = request.split('\n')[0].split(':')[1].split(',')[1]
        elif(rv['command'] == 'join'):
            rv['ip'] = request.split('\n')[0].split(':')[1].split(',')[0]
            rv['port'] = request.split('\n')[0].split(':')[1].split(',')[1]
        elif(rv['command'] == 'depart'):
            rv['id'] = request.split('\n')[0].split(':')[1]
        elif(rv['command'] == 'delete' or rv['command'] == 'query'):
            rv['key'] = request.split('\n')[0].split(':')[1]
        return rv

    def sendResponse(self,request,response):
        responseNodeIP = request.split('\n')[1]
        responseNodePort = int(request.split('\n')[2])
        if(self.ip == responseNodeIP and self.port == responseNodePort):
            return response
        requestID = request.split('\n')[3]
        conn = Remote(responseNodeIP,responseNodePort)
        conn.send('response:%s,%s' % (requestID,response))
        conn.close_connection()
        return None

    def hash(self,key):
        return int(hashlib.sha1((key).encode()).hexdigest(), 16) % ringSize

    def joinRing(self) -> None:
        conn = Remote(masterIP)
        msg = 'join:%s,%s' % (self.ip, self.port)
        conn.send(msg)
        conn.close_connection()

    def isResponsible(self, id) -> bool:
        rv = False
        if(self.id < self.previous.id):
            if(0 <= id <= self.id or self.previous.id < id < ringSize - 1):
                rv = True
        else:
            if(self.previous.id < id <= self.id):
                rv = True
        return rv

    def insert(self, request):
        requestData = self.parseRequest(request)
        if(self.isResponsible(self.hash(requestData['key']))):
            self.data[requestData['key']] = requestData['value']
            return self.sendResponse(request,'OK')
        else:
            print("I'm not responsible for id %s send to previous with ip %s" % (self.hash(requestData['key']),self.previous.ip))
            return self.sendToPrevious(request)

    def delete(self,request):
        requestData = self.parseRequest(request)
        if(self.isResponsible(self.hash(requestData['key']))):
            self.data.pop(requestData['key'])
            return self.sendResponse(requestData,'OK')
        else:
            return self.sendToNext(request)

    def redistributeData(self, targetNode) -> None:
        for key in self.data:
            key_hash = self.hash(key)
            if(not self.isResponsible(key_hash)):
                value = self.data.pop(key)
                targetNode.connection.send('insert:%s,%s' % (key, value))

    def depart(self, request):
        requestData = self.parseRequest(request)
        if(requestData['id'] == self.id):
            self.previous.connection('next:%s,%s|' % (self.next.ip, self.next.port))
            self.next.connection('prev:%s,%s|' % (self.previous.ip, self.previous.port))
            self.redistributeData(self.next)
            return self.sendResponse(request,'OK')
        else:
            return self.sendToNext(request)

    def query(self,request):
        requestData = self.parseRequest(request)
        if(self.isResponsible(self.hash(requestData['key']))):
            return self.sendResponse(request,self.data[requestData['key']])
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
        if(self.next is not self):
            self.next.connection.close_connection()
        self.next = Node(ip, port)
        self.next.connection = Remote(self.next.ip, self.next.port)
        print('Added %s as next' % ip)

    def setPrevious(self, ip, port=42069) -> None:
        if(self.previous is not self):
            self.previous.connection.close_connection()
        self.previous = Node(ip, port)
        self.previous.connection = Remote(self.previous.ip, self.previous.port)
        print('Added %s as previous' % ip)

    def __str__(self) -> None:
        return "(%s,%s,%s)-->" % (self.ip, self.port, self.id)

    def ping(self) -> None:
        print(str(self))
        if(self.next.ip != masterIP):
            self.next.connection.send('ping')


if __name__ == "__main__":
    ip = get_ip_address('eth1')
    print('My ip is %s' % ip)
    node = Node(ip)
