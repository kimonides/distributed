import socket
import hashlib
import json

ringSize = 10

def hash(key):
    return int(hashlib.sha1((key).encode()).hexdigest(), 16) % ringSize

masterIP = '192.168.1.5'
masterPort = 42069

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((masterIP,masterPort))

print('1)Join')
print('2)Depart')
print('3)Insert')
print('4)Delete')
print('5)Query')
print('6)Ping')
cmd = input('Input the number of the command you with to run:')

msg = {}

if(cmd=='1'):
    ip = input('IP:')
    port = input('Port:')
    msg['type'] = 'join'
    msg['join'] = {
        'ip':ip,
        'port':port
    }
elif(cmd=='2'):
    msg['type'] = 'depart'
    id = input('ID:')
    msg['depart'] = {
        'id':id
    }
elif(cmd=='3'):
    key = input('Key:')
    value = input('Value:')
    key_hash = hash(key)
    msg['type'] = 'insert'
    msg['insert'] = {
        'key':key_hash,
        'value':value
    }
elif(cmd=='4'):
    key = input('Key:')
    key_hash = hash(key)
    msg['type'] = 'delete'
    msg['delete'] = {
        'key':key_hash
    }
elif(cmd=='5'):
    key = input('Key:')
    if(key != '*'):
        key = hash(key)
    msg['type'] = 'query'
    msg['query'] = {
        'key':key
    }
elif(cmd=='6'):
    msg['type'] = 'ping'
    msg['ping'] = {}

msg['responseNodeIP'] = masterIP
msg['responseNodePort'] = masterPort
msg = json.dumps(msg)

print(repr('Sending %s' % msg))
socket.sendall(msg.encode())
print('Received %s' % socket.recv(1023).decode())


























# if(cmd=='1'):
#     ip = input('IP:')
#     port = input('Port:')
#     msg = 'join:%s,%s' % (ip,port)
# elif(cmd=='2'):
#     id = input('ID:')
#     msg = 'depart:%s' % id
# elif(cmd=='3'):
#     key = input('Key:')
#     value = input('Value:')
#     key_hash = hash(key)
#     msg = 'insert:%s,%s' % (key_hash,value)
# elif(cmd=='4'):
#     key = input('Key:')
#     key_hash = hash(key)
#     msg = 'delete:%s' % key_hash
# elif(cmd=='5'):
#     key = input('Key:')
#     if(key != '*'):
#         key = hash(key)
#     msg = 'query:%s' % key
# elif(cmd=='6'):
#     msg = 'ping:'

# msg += '\n%s\n%s' % (masterIP,masterPort)

# print(repr('Sending %s' % msg))
# socket.sendall(msg.encode())
# print('Received %s' % socket.recv(1023).decode())


