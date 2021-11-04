#!/usr/bin/env python3

from select import select
from socket import socket, AF_INET, SHUT_RDWR, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET
from sys import exit

SERVER_ADDRESS = ('localhost', 9000)

class Server:
  def __init__(self):
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setblocking(0)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(5)
    self.socket = server_socket

  def get_socket(self):
    return self.socket

  def accept_connection(self):
    client_socket, _ = self.socket.accept()
    client_socket.setblocking(0)
    return client_socket

  def disconnect(self, client_socket):
    client_socket.shutdown(SHUT_RDWR)
    client_socket.close()

def run_server(server):
  server_socket = server.get_socket()

  inputs            = [server_socket]
  outputs           = []

  while True:
    readable, writable, exceptional = select(inputs, outputs, inputs, 5)

    for ready_socket in readable:
      if ready_socket == server_socket:
        client_socket = server.accept_connection()
        inputs.append(client_socket)

      else:
        message = ready_socket.recv(1024).decode()

        if not message:
          server.disconnect(ready_socket)
          inputs.remove(ready_socket)
          break

        print('Received message: ' + message)
        
def main():
  server = Server()
  retval = run_server(server)
  exit(retval)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    exit(0)
