#!/usr/bin/env python3

from queue import Queue
from re import match, split, DOTALL
from socket import socket, AF_INET, SHUT_RDWR, SOCK_STREAM
import sys
from threading import Thread

SERVER_ADDRESS = ('localhost', 9000)
SUCCESS = 0
FAILURE = 1

client_socket = None
username = None
chats = {}

"""
  Chat
"""
class Chat:
  def __init__(self, partner):
    self.username = username
    self.partner = partner
    self.message_queue = Queue()

    window = Thread(target=self.__chat, args=(self.partner,), daemon=True)
    window.start()

  def __update_window(self):
    while True:
      message = self.message_queue.get(block=True, timeout=None)
      print('{}: {}'.format(self.partner, message))

  def __chat(self, partner):
    updater = Thread(target=self.__update_window, daemon=True)
    updater.start()

    while True:
      payload = input('Your message: ')
      if not payload: continue
      headers = 'event: outgoing\nusername: {}\nto: {}\n\n'.format(self.username, self.partner)
      client_socket.send(headers + payload)

  def load_message(self, message):
    self.message_queue.put_nowait(message)

"""
  listen()

  Listen for incomnig data from the server. Parse incoming data and dispatch the
  incoming user messages accordingly.
"""
def listen():
  while True:
    data = client_socket.receive()

    headers, payload = parse_incoming(data)
    event = headers['event']
    partner = headers['from']
    if event == 'incoming':
      if partner not in chats: chats[partner] = Chat(partner)
      chats[partner].load_message(payload)

def chat():
  partner = input('Enter the username of the user you wish to chat with: ')
  if not partner.isalnum(): return FAILURE

  if partner not in chats:
    chats[partner] = Chat(partner)

  return SUCCESS

"""
  show_messaging_menu()

  Prompt the logged in user for messaging actions. 
"""
def show_messaging_menu():
  # Spawn a new thread to listen for data pushes from the server
  listener = Thread(target=listen, daemon=True)
  listener.start()

  while True:
    # Display available options
    print('1. Enter `1` to open a chat with another user')
    print('2. Enter `2` to logout and exit')

    # Request user input
    action = input('What would you like to do? ')

    # Error checking on user input
    if not action.isdecimal(): continue
    action = int(action)

    # Open a chat with another user
    if action == 1:
      chat()

    # Logout and exit
    elif action == 2:
      client_socket.disconnect(SUCCESS)

"""
  ClientServerConnection

  A wrapper for the socket connecting the client and the server.
"""
class ClientServerConnection:
  def __init__(self, sock):
    self.socket = sock

  # Send messages to the server
  def send(self, message):
    return self.socket.send(message.encode())

  # Receive messages from the server
  # If no bytes of data received, then connection has been closed, so disconnect
  def receive(self, buffer_size = 1024):
    data = self.socket.recv(buffer_size)
    if not data:
      sys.stderr.write('The connection to the server has been closed! Please try again later.\n')
      self.disconnect(FAILURE)
    return data.decode()

  # Close the socket and exit the client
  def disconnect(self, code):
    if code == SUCCESS: self.socket.shutdown(SHUT_RDWR)
    self.socket.close()
    exit(code)

"""
  connect()

  Try to connect to the configured server. If connection is unsuccessful, exit.
"""
def connect(server_address):
  # Connect to the server
  try:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(server_address)

    global client_socket
    client_socket = ClientServerConnection(sock)

  # Failed to connect to server, exit
  except:
    sys.stderr.write('Unable to connect to the server\n')
    sys.exit(FAILURE)

"""
  parse_incoming()

  Parse the headers and the payload from the incoming data from the server.
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
    sys.stderr.write('Unable parse incoming data: ', data, '\n')
    sys.exit(FAILURE)

"""
  register()

  Accept user-inputted username and password and attempt to create a new account
  on the server with these credentials.
"""
def register():
  user = input('Username: ')
  pw = input('Password (insecure!): ')
  message = 'event: register\nusername: {}\npassword: {}\n\n'.format(user, pw)
  client_socket.send(message)

  response = client_socket.receive()

  headers, _ = parse_incoming(response)

  if headers['event'] == 'register' and headers['status'] == 'success':
    print('Registration succeeded!\n')
    return SUCCESS

  else:
    print('Registration failed!\n')
    return FAILURE

"""
  login()

  Accept user-inputted username and password and attempt to login to the server
  with these credentials.
"""
def login():
  user = input('Username: ')
  pw = input('Password (insecure!): ')
  message = 'event: login\nusername: {}\npassword: {}\n\n'.format(user, pw)
  client_socket.send(message)

  response = client_socket.receive()

  headers, _ = parse_incoming(response)

  if headers['event'] == 'login' and headers['status'] == 'success':
    global username
    username = user
    print('Login succeeded!\n')
    return SUCCESS

  else:
    print('Login failed!\n')
    return FAILURE

"""
  show_main_menu()

  Ask the user to login to an existing account or register a new account. Once
  a user logs in successfully, messaging features are unlocked.
"""
def show_main_menu():
  while True:
    # Display available options
    print('1. Enter `1` to login to an existing account')
    print('2. Enter `2` to register a new account')

    # Request user input
    action = input('What would you like to do? ')

    # Error checking on user input
    if not action.isdecimal(): continue
    action = int(action)

    # Login to an existing account
    if action == 1:
      login_status = login()
      if login_status == SUCCESS: show_messaging_menu()

    # Register a new account
    elif action == 2:
      register()

def main():
  connect(SERVER_ADDRESS)
  show_main_menu()
  exit(SUCCESS)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    exit(SUCCESS)
