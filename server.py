#!/usr/bin/env python3

from re import match, split, DOTALL
from select import select
import sqlite3
from socket import socket, AF_INET, SHUT_RDWR, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET

SERVER_ADDRESS = ('localhost', 9000)
SM_DATABASE = 'sm.db'

inputs = []
socket_connections = {} # key: socket, value: Connection
username_connections = {} # key: username, value: Connection


def parse_headers(match_headers):
  headers_dict = {}
  for line in match_headers.split('\n'):
    if not line: continue
    key, value = split(': ', line, 1)
    headers_dict[key] = value
  return headers_dict

def register_new_user(client_socket, username, password):
  try:
    connection = sqlite3.connect(USERS_DATABASE)
    cursor = connection.cursor()

    cursor.execute('''
      INSERT INTO users(username, password)
      VALUES(?,?)
      ''', (username, password))
    connection.commit()
  except:
    connection.close()
    client_socket.send('event: register\nstatus: fail\n\n'.encode())
  else:
    connection.close()
    client_socket.send('event: register\nstatus: success\n\n'.encode())

def client_login(connection_obj, username, password):
  client_socket = connection_obj.get_client_socket()

  try:
    connection = sqlite3.connect(USERS_DATABASE)
    cursor = connection.cursor()

    cursor.execute('''
      SELECT username FROM users
      WHERE username = ? AND password = ?
      ''', (username, password))
    data = cursor.fetchone()
  except:
    connection.close()
    client_socket.send('event: login\nstatus: fail\n\n'.encode())
    return None
  else:
    if data is None:
      connection.close()
      client_socket.send('event: login\nstatus: fail\n\n'.encode())
      return None
    else:
      connection.close()
      connection_obj.set_username(username)
      username_connections[username] = connection_obj
      client_socket.send('event: login\nstatus: success\n\n'.encode())
      return username

def relay_message(source, recipient, payload):
  message = 'event: incoming\nfrom: {}\n\n'.format(source) + payload
  username_connections[recipient].get_client_socket().send(message.encode())


class Connection:
  def __init__(self, server_socket):
    client_socket, _ = server_socket.accept()
    client_socket.setblocking(0)
    self.client_socket = client_socket
    socket_connections[self.client_socket] = self
    inputs.append(self.client_socket)

  def disconnect(self):
    self.client_socket.shutdown(SHUT_RDWR)
    self.client_socket.close()
    if self.client_socket in inputs: inputs.remove(self.client_socket)

  def get_client_socket(self):
    return self.client_socket

  def set_username(self, username):
    self.username = username

  def process_data(self):
    data = self.client_socket.recv(1024).decode()

    if not data: return self.disconnect()

    try:
      data_match = match('^(?P<headers>.*\n)\n(?P<payload>.*)$', data, flags=DOTALL)
      headers = parse_headers(data_match['headers'])

      event = headers['event']

      if event == 'outgoing':
        relay_message(self.username, headers['to'], data_match['payload'])

      elif event == 'login':
        result = client_login(self, headers['username'], headers['password'])

      elif event == 'register':
        register_new_user(self.client_socket, headers['username'], headers['password'])

    except:
      print('Error processing data')
      return

def makedb():
  conn = sqlite3.connect(SM_DATABASE)
  cursor = conn.cursor()

  cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
      username TEXT PRIMARY KEY,
      hsh_password TEXT NOT NULL
    )
  ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS msg_history(
      id INTEGER PRIMARY KEY,
      sender TEXT NOT NULL,
      recipient TEXT NOT NULL,
      hsh_message TEXT
    )
  ''')

  connection.commit()
  connection.close()

def initialize_server():
  server_socket = socket(AF_INET, SOCK_STREAM)
  server_socket.setblocking(0)
  server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
  server_socket.bind(SERVER_ADDRESS)
  server_socket.listen(5)
  inputs.append(server_socket)

  makedb()

  return server_socket

def run_server(server_socket):
  while True:
    readable, _, _ = select(inputs, [], [])

    for ready_socket in readable:
      if ready_socket == server_socket:
        connection = Connection(server_socket)

      else:
        connection = socket_connections[ready_socket]
        connection.process_data()
        
def main():
  server_socket = initialize_server()
  retval = run_server(server_socket)
  exit(retval)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    exit(0)
