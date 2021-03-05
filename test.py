from remote import Remote


# ip = input('IP: ')

#   responses
#   response: requestID,result
#
#   requests
#   insert:key,value\nResponseNodeIP\nResponseNodePort\nrequestID
#   

conn = Remote('192.168.1.5',42069)
msg = input('Message to send:\n')
# msg = 'join:192.168.1.1,42069\n192.168.1.5\n42069'
if(msg != 'ping'):
    msg = msg + '\n192.168.1.5\n42069'
print(repr('Sending %s' % msg))
conn.send(msg)
conn.receive()
conn.close_connection()
















# HOST = '192.168.1.5'  # The server's hostname or IP address
# PORT = 42069        # The port used by the server

# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.connect((HOST, PORT))
#     s.sendall(b'Hello, world')
#     data = s.recv(1024)
#     s.clo
# print(data.decode())

# conn = Remote('192.168.1.5',42069)

# loop = asyncio.get_event_loop()
# async def run():
#     await conn.open_connection()
# loop.run_until_complete(run())
# loop.close()

# conn.send('Hello World')


# async def tcp_echo_client(message, loop):
#     reader, writer = await asyncio.open_connection('192.168.1.5', 42069,loop=loop)

#     print('Send: %r' % message)
#     writer.write(message.encode())

#     data = await reader.read(255)
#     print('Received: %r' % data.decode())

#     print('Close the socket')
#     writer.close()


# message = 'Hello World!'
# loop = asyncio.get_event_loop()
# loop.run_until_complete(tcp_echo_client(message, loop))
# loop.close()