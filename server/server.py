#!/usr/bin/env python3

from re import match, split, DOTALL
from select import select
import sqlite3
import ssl
from SelfSignedCertificate import *
from socket import socket, AF_INET, SHUT_RDWR, SO_REUSEADDR, SOCK_STREAM, SOL_SOCKET
import sys

SERVER_ADDRESS = ('localhost', 9000)
USERS_DATABASE = 'users.db'
SUCCESS = 0
FAILURE = 1

inputs = []
socket_connections = {} # key: socket, value: Connection
username_connections = {} # key: username, value: Connection

"""
  parse_incoming()

  Parse the headers and the payload from the incoming data from the clients.
"""
def parse_incoming(data):
  try:
    # Scan for the headers and the payload in the incoming data
    data_match = match('^(?P<headers>.*\n)\n(?P<payload>.*)$', data, flags=DOTALL)

    # Create a dictionary for the headers and header values
    headers = {}
    for line in data_match['headers'].split('\n'):
      if not line: continue
      key, value = split(': ', line, 1)
      headers[key] = value

    # Optional payload in data
    payload = data_match['payload']

    return headers, payload

  # Failed to parse incomnig data, exit
  except:
    sys.stderr.write('Unable to parse incoming data: ', data, '\n')
    sys.exit(FAILURE)

"""
  register_new_user()

  Register a new user account in the SQL database.
"""
def register_new_user(client_socket, username, password):
  try:
    # Connect to the database
    connection = sqlite3.connect(USERS_DATABASE)
    cursor = connection.cursor()

    # Insert new user credentials and save the database
    cursor.execute('''
      INSERT INTO users(username, password)
      VALUES(?,?)
      ''', (username, password))
    connection.commit()

  # If any error arises, fail registration and notify client
  except:
    connection.close()
    client_socket.send('event: register\nstatus: failure\n\n'.encode())

  # Notify client of successful registration
  else:
    connection.close()
    client_socket.send('event: register\nstatus: success\n\n'.encode())

"""
  client_login()

  Authenticate a client by comparing the user-inputted username and password
  with the SQL database.
"""
def client_login(connection_obj, username, password):
  client_socket = connection_obj.get_client_socket()

  try:
    # Connect to the database
    connection = sqlite3.connect(USERS_DATABASE)
    cursor = connection.cursor()

    # Query for the username and password
    cursor.execute('''
      SELECT username FROM users
      WHERE username = ? AND password = ?
      ''', (username, password))
    data = cursor.fetchone()

  # If any error arises, fail authentication and notify the client
  except:
    connection.close()
    client_socket.send('event: login\nstatus: failure\n\n'.encode())
    return None

  else:
    # No record was returned, fail authentication and notify the client
    if data is None:
      connection.close()
      client_socket.send('event: login\nstatus: failure\n\n'.encode())
      return None

    # Notify the client of successful authentication
    else:
      connection.close()
      connection_obj.set_username(username)
      username_connections[username] = connection_obj
      client_socket.send('event: login\nstatus: success\n\n'.encode())
      return username

"""
  relay_message()

  Receive an incoming message from the source. Convert the incoming message into
  an outgoing message. Send the outgoing message to the recipient.
"""
def relay_message(source, recipient, payload):
  message = 'event: incoming\nfrom: {}\n\n'.format(source) + payload
  username_connections[recipient].get_client_socket().send(message.encode())

"""
  Connection

  A wrapper for socket connections between clients and the server.
"""
class Connection:
  def __init__(self, server_socket):
    client_socket, _ = server_socket.accept()
    client_socket.setblocking(0)
    self.client_socket = client_socket
    socket_connections[self.client_socket] = self
    inputs.append(self.client_socket)

  # Close the socket to the client
  def disconnect(self):
    self.client_socket.shutdown(SHUT_RDWR)
    self.client_socket.close()
    if self.client_socket in inputs: inputs.remove(self.client_socket)

  # Return the client socket
  def get_client_socket(self):
    return self.client_socket

  # Set the client's username after successful authentication
  def set_username(self, username):
    self.username = username

  # Process data incoming from the client
  def process_data(self):
    data = self.client_socket.recv(1024).decode()

    if not data: return self.disconnect()

    try:
      headers, payload = parse_incoming(data)

      event = headers['event']

      # The client has sent an outgoing message, forward it to the recipient
      if event == 'outgoing':
        relay_message(self.username, headers['to'], payload)

      # Authenticate the client
      elif event == 'login':
        client_login(self, headers['username'], headers['password'])

      # Register a new client
      elif event == 'register':
        register_new_user(self.client_socket, headers['username'], headers['password'])

    except:
      print('Error processing data')
      return

"""
  create_users_database()

  Create a SQL database to store usernames and passwords.
"""
def create_users_database():
  connection = sqlite3.connect(USERS_DATABASE)
  cursor = connection.cursor()

  # Create the database if it does not exist
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
      username TEXT PRIMARY KEY,
      password TEXT NOT NULL
    )
  ''')

  connection.commit()
  connection.close()

"""
  initialize_server()

  Initialize the server's socket and database.
"""
def initialize_server():
  ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
  ctx.load_cert_chain('./certificate.crt', './key.pem')
  sock = socket(AF_INET, SOCK_STREAM)
  server_socket = ctx.wrap_socket(sock)
  server_socket.setblocking(0)
  server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
  server_socket.bind(SERVER_ADDRESS)
  server_socket.listen(5)
  inputs.append(server_socket)

  create_users_database()

  return server_socket

def initialize_certificate():
  '''
  initialize_certificate()

  Signs a certificate to be used for server authentication via TLS.
  Creates two files that contain the certificate and the private key.
  The files are currently just named 'certificate.crt' and 'key.pem'
  
  TODO:
  Modify SelfSignedCertificate to load previously established certificates
  that are shared with the clients.
  '''
  cert = SelfSignedCertificate(SERVER_ADDRESS[0], b'passphrase')

"""
  run_server()

  Event loop for the server. Accept connections and data from clients.
"""
def run_server(server_socket):
  while True:
    readable, _, _ = select(inputs, [], [])

    # Check if there is any data coming from clients
    for ready_socket in readable:
      # Accept connections from new clients
      if ready_socket == server_socket:
        connection = Connection(server_socket)

      # Receive data from connected clients
      else:
        connection = socket_connections[ready_socket]
        connection.process_data()
        
def main():
  initialize_certificate()
  server_socket = initialize_server()
  run_server(server_socket)
  sys.exit(SUCCESS)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    sys.exit(SUCCESS)
