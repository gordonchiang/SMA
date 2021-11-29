from threading import Thread
import tkinter

import Chat
import ClientAuthentication
import MessageHistory

chats = {}
message_histories = {}

"""
  initialize_chat()

  Open a GUI window to allow user to initialize a new chat with a recipient.
"""
def initialize_chat(client_socket, main_menu):
  recipient_window = tkinter.Toplevel(main_menu)

  # Callback function to get the recipient's username and open the chat window
  def get_input(_):
    recipient = input_text.get()
    if recipient not in chats:
      chats[recipient] = Chat.Chat(client_socket, main_menu, recipient)
    chats[recipient].chat()
    recipient_window.destroy()

  # Load menu to select recipients with whom to chat
  label = tkinter.Label(recipient_window, text='Recipient').pack(side=tkinter.LEFT)
  input_text = tkinter.StringVar()
  recipient_entry = tkinter.Entry(recipient_window, textvariable=input_text)
  recipient_entry.pack(side=tkinter.RIGHT)
  recipient_entry.bind('<Return>', get_input)

"""
  initialize_message_history()

  Open a GUI window to allow user to open a message history with a specific
  reicipient.
"""
def initialize_message_history(username, main_menu):
  select_history_window = tkinter.Toplevel(main_menu)

  # Callback function to get the recipient's username and open the history window
  def view_history(_ = None):
    recipient = recipient_text.get()
    password = password_text.get()

    if recipient and password: message_histories[recipient] = MessageHistory.Reader(main_menu, username, recipient, password)

    select_history_window.destroy()

  # Load menu to load message history
  # Get history for recipient
  recipient_label = tkinter.Label(select_history_window, text='Recipient').grid(row=0, column=0)
  recipient_text = tkinter.StringVar()
  recipient_entry = tkinter.Entry(select_history_window, textvariable=recipient_text)
  recipient_entry.grid(row=0, column=1)

  # Authenticate user to view and decrypt history
  password_label = tkinter.Label(select_history_window, text='Password').grid(row=1, column=0)
  password_text = tkinter.StringVar()
  password_entry = tkinter.Entry(select_history_window, show='*', textvariable=password_text)
  password_entry.grid(row=1, column=1)
  password_entry.bind('<Return>', view_history)

  submit_button = tkinter.Button(select_history_window, text='Open History', command=view_history).grid(row=3, column=1)

"""
  listen()

  Listen for incoming data from the server. Parse incoming data and dispatch the
  incoming user messages accordingly.
"""
def listen(client_socket, main_menu):
  while True:
    data = client_socket.receive()

    headers, payload = client_socket.parse_incoming(data)
    event = headers['event']

    # Message from recipient
    if event == 'incoming':
      recipient = headers['from']
      if recipient not in chats: chats[recipient] = Chat(client_socket, main_menu, recipient)
      chats[recipient].load_message(recipient, headers['type'], payload)

    # Message from server reflecting the outgoing messaging back to client
    # indicating an error
    elif event == 'outgoing' and headers['status'] == 'failure' and headers['type'] == 'server':
      recipient = headers['to']
      if recipient not in chats: chats[recipient] = Chat(client_socket, main_menu, recipient)
      chats[recipient].load_message(recipient, headers['type'], payload)

def delete_account(client_socket, main_menu):
  delete_account_box = tkinter.Toplevel(main_menu)

  # Callback function to delete the currently logged in account
  def del_acc():
    username = username_text.get()
    password = password_text.get()
    repeat_password = repeat_password_text.get()

    if username and password and repeat_password:
      if not password == repeat_password or not client_socket.get_username() == username:
        tkinter.messagebox.showinfo('Error', 'Incorrect credentials!')
        delete_account_box.destroy()
      else:
        if confirm_deletion.get() is False:
          tkinter.messagebox.showinfo('Error', 'Account deletion not confirmed!')
          delete_account_box.destroy()
        else:
          delete_success = ClientAuthentication.delete_account(client_socket, password)
          if delete_success is True:
            tkinter.messagebox.showinfo('Success', 'Your account {} has been deleted!'.format(client_socket.get_username()))
            ClientAuthentication.logout(client_socket)
            delete_account_box.destroy()
          else:
            tkinter.messagebox.showinfo('Error', 'Account deletion failed!')
            delete_account_box.destroy()

  # Load menu to delete account
  # Get the username
  username_label = tkinter.Label(delete_account_box, text='Username').grid(row=0, column=0)
  username_text = tkinter.StringVar()
  username_entry = tkinter.Entry(delete_account_box, textvariable=username_text)
  username_entry.grid(row=0, column=1)

  # Get the password
  password_label = tkinter.Label(delete_account_box, text='Password').grid(row=1, column=0)
  password_text = tkinter.StringVar()
  password_entry = tkinter.Entry(delete_account_box, show='*', textvariable=password_text)
  password_entry.grid(row=1, column=1)

  repeat_password_label = tkinter.Label(delete_account_box, text='Repeat Password').grid(row=2, column=0)
  repeat_password_text = tkinter.StringVar()
  repeat_password_entry = tkinter.Entry(delete_account_box, show='*', textvariable=repeat_password_text)
  repeat_password_entry.grid(row=2, column=1)

  # Checkbox to confirm deletion
  confirm_deletion = tkinter.BooleanVar()
  confirm_deletion_button = tkinter.Checkbutton(delete_account_box, text='Confirm account deletion', variable=confirm_deletion, onvalue=True, offvalue=False).grid(row=3, column=0)

  submit_button = tkinter.Button(delete_account_box, text='Delete Account', command=del_acc).grid(row=3, column=1)

"""
  show_main_menu()

  Prompt the logged in user for messaging actions.
"""
def show_main_menu(login_menu, client_socket):
  main_menu = tkinter.Toplevel(login_menu)

  username = client_socket.get_username()

  # Style chat menu window
  main_menu.geometry('300x150')
  main_menu.title('{} - main menu'.format(username))
  tkinter.Label(main_menu, text='Logged in as: {}'.format(username)).pack(fill=tkinter.X)

  # Spawn a new thread to listen for data pushes from the server
  listener = Thread(target=listen, args=(client_socket,main_menu), daemon=True)
  listener.start()

  chat_button = tkinter.Button(main_menu, text='Chat', command=lambda: initialize_chat(client_socket, main_menu)).pack()
  message_history_button = tkinter.Button(main_menu, text='Message History', command=lambda: initialize_message_history(username, main_menu)).pack()
  delete_account_button = tkinter.Button(main_menu, text='Delete Account', command=lambda: delete_account(client_socket, main_menu)).pack()
  exit_button = tkinter.Button(main_menu, text='Exit', command=client_socket.disconnect).pack(side=tkinter.BOTTOM)
