#!/usr/bin/env python3

from socket import socket, AF_INET, SHUT_RDWR, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET
from sys import exit

SERVER_ADDRESS = ('localhost', 9000)

class Client:
  def __init__(self):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.socket = client_socket

  def connect(self, server):
    self.socket.connect(server)

  def disconnect(self):
    self.socket.shutdown(SHUT_RDWR)
    self.socket.close()
    return 0

  def send(self, message):
    self.socket.send(message.encode())

def run_client(client):
  while True:
    message = input('Your message: ')
    if message == '/exit': return client.disconnect()
    client.send(message)

def main():
  client = Client()
  client.connect(SERVER_ADDRESS)
  retval = run_client(client)
  exit(retval)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    exit(0)
