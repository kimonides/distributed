from remote import Remote
from server import Server

import hashlib
import socket
import fcntl
import struct
from uuid import uuid4
import json

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
        if(self.ip == get_ip_address('eth1')):
            self.server = Server(self.ip, self)

    def send(self,request,targetNode):
        requestID = None
        if 'requestID' not in request:
            requestID = uuid4()
            request['requestID'] = str(requestID)
        print('Sending %s to %s' % (repr(request),self.next.ip))
        targetNode.connection.send(json.dumps(request))
        return requestID

    def sendResponse(self,request,response):
        responseNodeIP = request['responseNodeIP']
        responseNodePort = request['responseNodePort']
        if(self.ip == responseNodeIP and self.port == responseNodePort):
            return response
        try:
            requestID = request['requestID']
        except:
            return None
        conn = Remote(responseNodeIP,responseNodePort)
        res = json.dumps({'type':'response','requestID':requestID,'response':response})
        conn.send(res)
        return None

    def hash(self,key):
        return int(hashlib.sha1((key).encode()).hexdigest(), 16) % ringSize

    def redistribute(self,request) -> None:
        key_hash = request['redistribute']['key']
        value = request['redistribute']['value']
        self.data[key_hash] = value

    def insert(self, request):
        hash_key = int(request['insert']['key'])
        value = request['insert']['value']
        if(self.isResponsible(hash_key)):
            self.data[hash_key] = value
            print("I'm responsible for insert with hash key %s and value %s" % (hash_key,value))
            return self.sendResponse(request,'OK')
        else:
            print("I'm not responsible for id %s send to previous with ip %s" % (hash_key,self.previous.ip))
            return self.send(request,self.previous)

    def delete(self,request):
        hash_key = request['delete']['key']
        if(self.isResponsible(hash_key)):
            self.data.pop(hash_key)
            return self.sendResponse(request,'OK')
        else:
            return self.send(request,self.next)

    def isResponsible(self, hash) -> bool:
        hash = int(hash)
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
                targetNode.connection.send(json.dumps({'type':'redistribute','redistribute':{'key':key,'value':value}}))

    def depart(self, request):
        if(request['depart']['id'] == self.id):
            msg = json.dumps({ 'type':'next','ip':self.next.ip,'port':self.next.port })
            self.previous.connection.send(msg)
            msg = json.dumps({ 'type':'prev','ip':self.previous.ip,'port':self.previous.port })
            self.next.connection.send(msg)
            self.redistributeData(self.next,force=True)
            return self.sendResponse(request,'OK')
        else:
            return self.send(request,self.next)



    def query(self,request):
        requestData = json.dumps(request)
        hash_key = requestData['query']['key']
        if(self.isResponsible(hash_key)):
            if hash_key in self.data:
                resp = 'Query result is %s from %s with id %s' % (self.data[hash_key],self.ip,self.id)
                return self.sendResponse(request,resp)
            else:
                return self.sendResponse(request,"Key hash %s doesn't exist in the DHT" % hash_key)
        else:
            return self.send(request,self.next)

    def join(self, request):
        ip = request['join']['ip']
        port = request['join']['port']
        joinID = self.hash('%s:%s' % (ip,port))
        if(self.previous.id < joinID < self.id or self.previous is self):
            oldPrevIP = self.previous.ip
            oldPrevPort = self.previous.port
            if(self.previous is self):
                self.setNext(ip, port)
            else:
                self.previous.connection.send(json.dumps({ 'type':'next','ip':ip,'port':port }))
            self.setPrevious(ip, port)
            self.previous.connection.send(json.dumps({ 'type':'prev','ip':oldPrevIP,'port':oldPrevPort }))
            self.previous.connection.send(json.dumps({ 'type':'next','ip':self.ip,'port':self.port }))

            self.redistributeData(self.previous)
            return self.sendResponse(request,'OK')
        else:
            return self.send(request,self.next)

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
            response = request['response']
            return self.sendResponse(request,response)
        else:
            if('response' in request):
                request['response'] += str(self)
            else:
                request['response'] = str(self)
            return self.send(request,self.next)


if __name__ == "__main__":
    ip = get_ip_address('eth1')
    print('My ip is %s' % ip)
    node = Node(ip)

