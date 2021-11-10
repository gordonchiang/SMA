#!/usr/bin/env python3

from queue import Queue
from re import match, split, DOTALL
from socket import socket, AF_INET, SHUT_RDWR, SOCK_STREAM
import sys
from threading import Thread
import tkinter

SERVER_ADDRESS = ('localhost', 9000)
SUCCESS = 0
FAILURE = 1

client_socket = None
username = None
chats = {}

"""
  Chat

  A wrapper to group messages in the same conversations (i.e., to the same
  recipient) and to power the GUI.
"""
class Chat:
  def __init__(self, partner):
    self.username = username
    self.partner = partner
    self.message_queue = Queue()
    self.conversation = ''

  # Open a chat window: accept input to send as messages and update the window
  # with incoming messages
  def chat(self):
    chat_window = tkinter.Toplevel(root)
  
    # Callback to get input from user to send to partner
    def get_input(_):
      payload = input_text.get()
      message_entry.delete(0, tkinter.END) # Clear input field
      headers = 'event: outgoing\nusername: {}\nto: {}\n\n'.format(self.username, self.partner)
      client_socket.send(headers + payload)
      self.load_message('{}: {}'.format(self.username, payload))

    # Callback to update the chat window with messages every second
    def display_conversation():
      while not self.message_queue.empty():
        try:
          text = self.message_queue.get_nowait()
          conversation.insert(tkinter.END, text)
        except:
          continue

      chat_window.after(1000, display_conversation)

    # Create a Text widget to display the messages
    conversation = tkinter.Text(chat_window)
    conversation.insert(tkinter.END, self.conversation)
    conversation.update()
    conversation.pack()

    # Periodically update the messages
    display_conversation()
    
    # Request input from the user
    label = tkinter.Label(chat_window, text='Message').pack()
    input_text = tkinter.StringVar()
    message_entry = tkinter.Entry(chat_window, textvariable=input_text)
    message_entry.pack()
    message_entry.bind('<Return>', get_input)

  # Queue messages so they get loaded into the chat window in order
  def load_message(self, message):
    self.message_queue.put_nowait(message + '\n')

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
      chats[partner].load_message('{}: {}'.format(partner, payload))

"""
  chat()

  Initialize a new chat with a partner.
"""
def chat(root):
  partner_window = tkinter.Toplevel(root)

  # Request the partner's username and open the chat window
  def get_input(_):
    partner = input_text.get()
    if partner not in chats:
      chats[partner] = Chat(partner)
    chats[partner].chat()
    partner_window.destroy()

  label = tkinter.Label(partner_window, text='Partner' ).pack()
  input_text = tkinter.StringVar()
  partner_entry = tkinter.Entry(partner_window, textvariable=input_text)
  partner_entry.pack()
  partner_entry.bind('<Return>', get_input)

"""
  show_messaging_menu()

  Prompt the logged in user for messaging actions. 
"""
def show_messaging_menu():
  # Spawn a new thread to listen for data pushes from the server
  listener = Thread(target=listen, daemon=True)
  listener.start()

  global root
  root = tkinter.Tk()

  chat_button = tkinter.Button(root, text='Chat', command=lambda: chat(root)).pack()
  exit_button = tkinter.Button(root, text='Exit', command=lambda: client_socket.disconnect(SUCCESS)).pack()

  root.mainloop()

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
