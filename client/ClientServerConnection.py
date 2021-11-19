from re import match, split, DOTALL
from socket import SHUT_RDWR
import sys

"""
  ClientServerConnection

  A wrapper for the socket connecting the client and the server.
"""
class ClientServerConnection:
  def __init__(self, sock):
    self.socket = sock

  def set_username(self, username):
    self.username = username

  def get_username(self):
    return self.username

  # Send messages to the server
  def send(self, message):
    return self.socket.send(message.encode())

  # Receive messages from the server
  # If no bytes of data received, then connection has been closed, so disconnect
  def receive(self, buffer_size = 1024*30):
    try:
      data = self.socket.recv(buffer_size)
      if not data:
        sys.stderr.write('The connection to the server has been closed! Please try again later.\n')
        self.disconnect()
      return data.decode()
    except ConnectionResetError as e:
      sys.stderr.write('The connection to the server has been closed! Please try again later.\n')
      return self.disconnect()

  # Close the socket and exit the client
  def disconnect(self):
    try:
      self.socket.shutdown(SHUT_RDWR)
    except:
      pass
    self.socket.close()
    sys.exit(1)

  """
    parse_incoming()

    Parse the headers and the payload from the incoming data from the server.
  """
  @staticmethod
  def parse_incoming(data):
    try:
      # Scan for the headers and the payload in the incoming data
      data_match = match('^(?P<headers>.*?\n)\n(?P<payload>.*)$', data, flags=DOTALL)

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
    except Exception as e:
      sys.stderr.write('Unable to parse incoming data\n')
      print(e)
      sys.exit(1)
