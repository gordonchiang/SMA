from re import match, split, DOTALL
import sys
from socket import SHUT_RDWR
from ServerAuthentication import *

username_connections = {} # key: username, value: Connection

"""
  Connection

  A wrapper for socket connections between clients and the server.
"""
class Connection:
  def __init__(self, server_socket, users_database):
    client_socket, _ = server_socket.accept()
    client_socket.setblocking(0)
    self.client_socket = client_socket
    self.users_database = users_database
    self.username = None

  # Close the socket to the client
  def disconnect(self):
    try:
      self.client_socket.shutdown(SHUT_RDWR)
    except:
      pass
    self.client_socket.close()
    return 1

  # Return the client socket
  def get_client_socket(self):
    return self.client_socket

  # Set the client's username after successful authentication
  def set_username(self, username):
    self.username = username

  # Process data incoming from the client
  def process_data(self):
    try:
      # Retrieve data from socket
      data = self.client_socket.recv(1024).decode()

      # Connection closed by client
      if not data: return self.disconnect()

      headers, payload = self.parse_incoming(data)

      event = headers['event']

      # The client has sent an outgoing message, forward it to the recipient
      if event == 'outgoing':
        self.relay_message(headers['to'], payload)

      # Authenticate the client
      elif event == 'login':
        client_login(self, self.users_database, headers['username'], headers['password'])
        if self.username: username_connections[self.username] = self

      # Register a new client
      elif event == 'register':
        register_new_user(self.client_socket, self.users_database, headers['username'], headers['password'])

      # Delete a user's account
      elif event == 'delete':
        delete_user(self.client_socket, self.users_database, headers['username'], headers['password'])

    # Connection closed by client
    except ConnectionResetError as e:
      return self.disconnect()

    except Exception as e:
      print('Error processing data')
      print(e)

  """
    relay_message()

    Receive an incoming message from the source. Convert the incoming message into
    an outgoing message. Send the outgoing message to the recipient.
  """
  def relay_message(self, recipient, payload):
    message = 'event: incoming\nfrom: {}\n\n'.format(self.username) + payload
    username_connections[recipient].get_client_socket().send(message.encode())

  """
    parse_incoming()

    Parse the headers and the payload from the incoming data from the clients.
  """
  @staticmethod
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

    # Failed to parse incoming data, exit
    except:
      sys.stderr.write('Unable to parse incoming data: ', data, '\n')
      sys.exit(1)
