#!/usr/bin/env python3

from re import match, split, DOTALL
from socket import socket, AF_INET, SHUT_RDWR, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET
from sys import exit
import threading

SERVER_ADDRESS = ('localhost', 9000)

def parse_headers(match_headers):
  headers_dict = {}
  for line in match_headers.split('\n'):
    if not line: continue
    key, value = split(': ', line, 1)
    headers_dict[key] = value
  return headers_dict

class Client:
  def __init__(self):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.socket = client_socket

  def connect(self, server):
    self.socket.connect(server)

  def login(self):
    username = input('Username: ')
    self.username = username
    password = input('Password (insecure!): ')
    message = 'event: login\nusername: {}\npassword: {}\n\n'.format(username, password)
    self.send(message)

    response = self.receive()

    data_match = match('^(?P<headers>.*\n)\n(?P<payload>.*)$', response, flags=DOTALL)
    headers = parse_headers(data_match['headers'])

    try:
      if headers['event'] == 'login' and headers['status'] == 'success':
        print('Login succeeded!')
        return 0
      else:
        print('Login failed!')
        return 1
    except:
      print('Login failed!')
      return 1

  def register(self):
    username = input('Username: ')
    password = input('Password (insecure!): ')
    message = 'event: register\nusername: {}\npassword: {}\n\n'.format(username, password)
    self.send(message)

    response = self.receive()
    
    data_match = match('^(?P<headers>.*\n)\n(?P<payload>.*)$', response, flags=DOTALL)
    headers = parse_headers(data_match['headers'])

    try:
      if headers['event'] == 'register' and headers['status'] == 'success':
        print('Registration succeeded!')
        return 0
      else:
        print('Registration failed!')
        return 1
    except:
      print('Registration failed!')
      return 1

  def disconnect(self):
    self.socket.shutdown(SHUT_RDWR)
    self.socket.close()
    return 0

  def send(self, message):
    self.socket.send(message.encode())

  def outgoing(self, message, recipient):
    headers = 'event: outgoing\nusername: {}\nto: {}\n\n'.format(self.username, recipient)
    self.send(headers + message)

  def receive(self, buffer = 1024):
    data = self.socket.recv(buffer).decode()
    if not data: exit(self.disconnect())
    return data

  def listen(self):
    data = self.receive()
    data_match = match('^(?P<headers>.*\n)\n(?P<payload>.*)$', data, flags=DOTALL)
    headers = parse_headers(data_match['headers'])
    event = headers['event']
    if event == 'incoming':
      print('From {}: {}\n'.format(headers['from'], data_match['payload']))

def listen(client):
  while True:
    client.listen()

def run_client(client):
  listener = threading.Thread(target=listen, args=(client,), daemon=True)
  listener.start()

  while True:
    recipient = input('Recipient: ')
    message = input('Your message: ')
    if message == '/exit': return client.disconnect()
    client.outgoing(message, recipient)

def show_menu(client):
  while True:
    print("1. Enter 'register' to register a new account")
    print("2. Enter 'login' to login to an existing account")
    action = input('What would you like to do? ')
    if action == 'login':
      if client.login() == 0:
        return 0
    elif action == 'register':
      client.register()

def main():
  client = Client()
  client.connect(SERVER_ADDRESS)
  show_menu(client)
  retval = run_client(client)
  exit(retval)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    exit(0)
