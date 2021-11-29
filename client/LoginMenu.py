import json
import os
from pathlib import Path
import sys
import tkinter
import tkinter.messagebox

import ClientAuthentication
import ClientChat
import MessageHistoryEncryption

class LoginMenu:
  def __init__(self, client_socket):
    self.client_socket = client_socket
    self.login_menu = tkinter.Tk()

    # Style chat menu window
    self.login_menu.geometry('300x100')
    self.login_menu.title('Main Menu')
    tkinter.Label(self.login_menu, text='Main Menu').pack(fill=tkinter.X)

    login_button = tkinter.Button(self.login_menu, text='Login', command=self.__login).pack()
    register_button = tkinter.Button(self.login_menu, text='Register', command=self.__register).pack()
    exit_button = tkinter.Button(self.login_menu, text='Exit', command=lambda: sys.exit(0)).pack()

    # Exit if socket to server not created
    if self.client_socket is None:
      tkinter.messagebox.showinfo('Error', 'Unable to connect to the server!')
      sys.exit(1)

    self.login_menu.mainloop()

  def __register(self):
    register_window = tkinter.Toplevel(self.login_menu)

    # Callback function to register a new account with the server
    def register(_ = None):
      username = username_text.get()
      password = password_text.get()
      repeat_password = repeat_password_text.get()

      if username and password and repeat_password:
        if not password == repeat_password:
          tkinter.messagebox.showinfo('Error', 'Passwords do not match!')
          register_window.destroy()
        else:
          register_success = ClientAuthentication.register(self.client_socket, username, password)
          if register_success is True:
            tkinter.messagebox.showinfo('Success', 'Your account {} has been registered!'.format(username))
            register_window.destroy()
          else:
            tkinter.messagebox.showinfo('Error', 'Registration failed!')
            register_window.destroy()

    # Load menu to register
    # Get the username
    username_label = tkinter.Label(register_window, text='Username').grid(row=0, column=0)
    username_text = tkinter.StringVar()
    username_entry = tkinter.Entry(register_window, textvariable=username_text)
    username_entry.grid(row=0, column=1)

    # Get the password
    password_label = tkinter.Label(register_window, text='Password').grid(row=1, column=0)
    password_text = tkinter.StringVar()
    password_entry = tkinter.Entry(register_window, show='*', textvariable=password_text)
    password_entry.grid(row=1, column=1)

    repeat_password_label = tkinter.Label(register_window, text='Repeat Password').grid(row=2, column=0)
    repeat_password_text = tkinter.StringVar()
    repeat_password_entry = tkinter.Entry(register_window, show='*', textvariable=repeat_password_text)
    repeat_password_entry.grid(row=2, column=1)
    repeat_password_entry.bind('<Return>', register)

    submit_button = tkinter.Button(register_window, text='Register', command=register).grid(row=3, column=1)

  def __login(self):
    login_window = tkinter.Toplevel(self.login_menu)

    # Callback function to login to the server with username and password
    def login(_ = None):
      username = username_text.get()
      password = password_text.get()

      if username and password:
        login_success = ClientAuthentication.login(self.client_socket, username, password)
        if login_success is True:
          self.__create_user_config(self.client_socket.get_username(), password)
          ClientChat.show_main_menu(self.login_menu, self.client_socket)
          self.login_menu.withdraw()
          login_window.destroy()
        else:
          tkinter.messagebox.showinfo('Error', 'Login failed!')
          login_window.destroy()

    # Load menu to login
    # Get the username
    username_label = tkinter.Label(login_window, text='Username').grid(row=0, column=0)
    username_text = tkinter.StringVar()
    username_entry = tkinter.Entry(login_window, textvariable=username_text)
    username_entry.grid(row=0, column=1)

    # Get the password
    password_label = tkinter.Label(login_window, text='Password').grid(row=1, column=0)
    password_text = tkinter.StringVar()
    password_entry = tkinter.Entry(login_window, show='*', textvariable=password_text)
    password_entry.grid(row=1, column=1)
    password_entry.bind('<Return>', login)

    submit_button = tkinter.Button(login_window, text='Login', command=login).grid(row=3, column=1)

  # Creates the user's config.json where keys are stored
  def __create_user_config(self, username, password):
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
