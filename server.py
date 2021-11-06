#!/usr/bin/env python3

from re import match, split, DOTALL
from select import select
import sqlite3
from socket import socket, AF_INET, SHUT_RDWR, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET

SERVER_ADDRESS = ('localhost', 9000)

connected_clients = {}
logged_in_users = {}

def parse_headers(match_headers):
  headers_dict = {}
  for line in match_headers.split('\n'):
    if not line: continue
    key, value = split(': ', line, 1)
    headers_dict[key] = value
  return headers_dict

def register_new_user(username, password):
  connection = sqlite3.connect('users.db')
  cursor = connection.cursor()

  try:
    cursor.execute('''
      INSERT INTO users(username, password)
      VALUES(?,?)
      ''', (username, password))
    connection.commit()
  except:
    connection.close()
    return 1
  else:
    connection.close()
    return 0

def client_login(username, password):
  connection = sqlite3.connect('users.db')
  cursor = connection.cursor()

  try:
    cursor.execute('''
      SELECT username FROM users
      WHERE username = ? AND password = ?
      ''', (username, password))
    data = cursor.fetchone()
    if data is None:
      return 1
    else:
      return username
  except:
    connection.close()
    return 1

class Connection:
  def __init__(self, server_socket):
    client_socket, _ = server_socket.accept()
    client_socket.setblocking(0)
    self.client_socket = client_socket

  def disconnect(self):
    self.client_socket.shutdown(SHUT_RDWR)
    self.client_socket.close()
    return self.client_socket

  def get_client_socket(self):
    return self.client_socket

  def process_data(self, data):
    if not data:
      client_socket = self.disconnect()
      connected_clients.pop(client_socket, None)
      return

    print(repr(data))
    data_match = match('^(?P<headers>.*\n)\n(?P<payload>.*)$', data, flags=DOTALL)
    headers = parse_headers(data_match['headers'])

    event = headers['event']
    if event == 'login':
      result = client_login(headers['username'], headers['password'])
      self.get_client_socket().send(str(result).encode())
      if result == headers['username']:
        self.username = result
        logged_in_users[result] = self
    elif event == 'register':
      result = register_new_user(headers['username'], headers['password'])
      self.get_client_socket().send(str(result).encode())
    elif event == 'outgoing':
      recipient = headers['recipient']
      payload = data_match['payload']
      print('Received message: ' + payload)
      message = 'event: incoming\nfrom: {}\n\n'.format(self.username) + payload
      logged_in_users[recipient].get_client_socket().send(message.encode())

def initialize_server():
  server_socket = socket(AF_INET, SOCK_STREAM)
  server_socket.setblocking(0)
  server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
  server_socket.bind(SERVER_ADDRESS)
  server_socket.listen(5)
  return server_socket

def create_database():
  connection = sqlite3.connect('users.db')
  cursor = connection.cursor()

  cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
      username TEXT PRIMARY KEY,
      password TEXT NOT NULL
    )
  ''')

  connection.commit()
  connection.close()

def run_server(server_socket):
  inputs            = [server_socket]
  # outputs           = []

  while True:
    readable, writable, exceptional = select(inputs, inputs, inputs)

    for ready_socket in readable:
      if ready_socket == server_socket:
        connection = Connection(server_socket)
        client_socket = connection.get_client_socket()
        connected_clients[client_socket] = connection
        inputs.append(client_socket)

      else:
        data = ready_socket.recv(1024).decode()
        connection = connected_clients[ready_socket]
        connection.process_data(data)
        
def main():
  server_socket = initialize_server()
  create_database()
  retval = run_server(server_socket)
  exit(retval)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    exit(0)
