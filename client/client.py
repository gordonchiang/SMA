#!/usr/bin/env python3

import json
from pathlib import Path
import os
from socket import socket, AF_INET, SOCK_STREAM
import ssl
import sys
import tkinter
import tkinter.messagebox

import ClientAuthentication
import ClientChat
import ClientServerConnection
import MessageHistoryEncryption

"""
  connect()

  Try to connect to the configured server. If connection is unsuccessful, exit.
"""
def connect(server_address):
  # Connect to the server
  try:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations('certificate.crt')
    pre_sock = socket(AF_INET, SOCK_STREAM)
    sock = ctx.wrap_socket(pre_sock, server_hostname=server_address[0])
    sock.connect(server_address)

    return ClientServerConnection.ClientServerConnection(sock)

  # Failed to connect to server
  except:
    sys.stderr.write('Unable to connect to the server\n')
    return None

"""
    create_user_config()

    Creates the user's config.json where keys are stored.
"""
def create_user_config(username, password):
    # Build the path to the user's config file
    root_dir = os.path.dirname(os.path.realpath(__file__))
    user_dir = Path(root_dir + '/{}'.format(username))
    user_config_path = Path(root_dir + '/{}/config.json'.format(username))

    # Validate username input; enforce child path of ./client/
    if not user_config_path.is_relative_to(root_dir):
        return None

    # Create the yser directory for username if it doesn't exist
    try:
        os.makedirs(user_dir)
    except FileExistsError:
        pass

    # Create a new config file if it doesn't exist
    if os.path.exists(user_config_path):
        return None

    # Generate the private and pubic RSA keys' PEMs to write to the config file
    private_pem, public_pem = MessageHistoryEncryption.MessageHistoryEncryption().generate_pems(password)

    data = {}
    data['private_pem'] = private_pem.decode('utf-8')
    data['public_pem'] = public_pem.decode('utf-8')

    # Write the config file
    config_fd = open(user_config_path, 'w')
    json.dump(data, config_fd, indent=2)
    config_fd.close()

def login_prompt(login_menu, client_socket):
  login_box = tkinter.Toplevel(login_menu)

  # Callback function to login to the server with username and password
  def login(_ = None):
    username = username_text.get()
    password = password_text.get()

    if username and password:
      login_success = ClientAuthentication.login(client_socket, username, password)
      if login_success is True:
        ClientChat.show_main_menu(login_menu, client_socket)
        login_menu.withdraw()
        login_box.destroy()
      else:
        tkinter.messagebox.showinfo('Error', 'Login failed!')
        login_box.destroy()

  # Load menu to login
  # Get the username
  username_label = tkinter.Label(login_box, text='Username').grid(row=0, column=0)
  username_text = tkinter.StringVar()
  username_entry = tkinter.Entry(login_box, textvariable=username_text)
  username_entry.grid(row=0, column=1)

  # Get the password
  password_label = tkinter.Label(login_box, text='Password').grid(row=1, column=0)
  password_text = tkinter.StringVar()
  password_entry = tkinter.Entry(login_box, show='*', textvariable=password_text)
  password_entry.grid(row=1, column=1)
  password_entry.bind('<Return>', login)

  submit_button = tkinter.Button(login_box, text='Login', command=login).grid(row=3, column=1)

def register_prompt(login_menu, client_socket):
  register_box = tkinter.Toplevel(login_menu)

  # Callback function to register a new account with the server
  def register(_ = None):
    username = username_text.get()
    password = password_text.get()
    repeat_password = repeat_password_text.get()

    if username and password and repeat_password:
      if not password == repeat_password:
        tkinter.messagebox.showinfo('Error', 'Passwords do not match!')
        register_box.destroy()
      else:
        register_success = ClientAuthentication.register(client_socket, username, password)
        if register_success is True:
          tkinter.messagebox.showinfo('Success', 'Your account {} has been registered!'.format(username))
          register_box.destroy()
        else:
          tkinter.messagebox.showinfo('Error', 'Registration failed!')
          register_box.destroy()

  # Load menu to register
  # Get the username
  username_label = tkinter.Label(register_box, text='Username').grid(row=0, column=0)
  username_text = tkinter.StringVar()
  username_entry = tkinter.Entry(register_box, textvariable=username_text)
  username_entry.grid(row=0, column=1)

  # Get the password
  password_label = tkinter.Label(register_box, text='Password').grid(row=1, column=0)
  password_text = tkinter.StringVar()
  password_entry = tkinter.Entry(register_box, show='*', textvariable=password_text)
  password_entry.grid(row=1, column=1)

  repeat_password_label = tkinter.Label(register_box, text='Repeat Password').grid(row=2, column=0)
  repeat_password_text = tkinter.StringVar()
  repeat_password_entry = tkinter.Entry(register_box, show='*', textvariable=repeat_password_text)
  repeat_password_entry.grid(row=2, column=1)
  repeat_password_entry.bind('<Return>', register)

  submit_button = tkinter.Button(register_box, text='Register', command=register).grid(row=3, column=1)

def main():
  login_menu = tkinter.Tk()

  with open("./client/config.json") as config_file:
    config = json.load(config_file)

  # Connect to the server
  client_socket = connect((config['server']['ip'], config['server']['port']))

  # Style chat menu window
  login_menu.geometry('300x100')
  login_menu.title('Main Menu')
  tkinter.Label(login_menu, text='Main Menu').pack(fill=tkinter.X)

  login_button = tkinter.Button(login_menu, text='Login', command=lambda: login_prompt(login_menu, client_socket)).pack()
  register_button = tkinter.Button(login_menu, text='Register', command=lambda: register_prompt(login_menu, client_socket)).pack()
  exit_button = tkinter.Button(login_menu, text='Exit', command=lambda: sys.exit(0)).pack()

  # Exit if socket to server not created
  if client_socket is None:
    tkinter.messagebox.showinfo('Error', 'Unable to connect to the server!')
    sys.exit(1)

  login_menu.mainloop()

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    sys.exit(0)
