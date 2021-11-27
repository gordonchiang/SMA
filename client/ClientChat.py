from threading import Thread
import tkinter
import Chat

chats = {}

"""
  initialize_chat()

  Open a GUI window to allow user to initialize a new chat with a recipient.
"""
def initialize_chat(client_socket, root):
  recipient_window = tkinter.Toplevel(root)

  # Callback function to get the recipient's username and open the chat window
  def get_input(_):
    recipient = input_text.get()
    if recipient not in chats:
      chats[recipient] = Chat.Chat(client_socket, root, recipient)
    chats[recipient].chat()
    recipient_window.destroy()

  # Load menu to select recipients with whom to chat
  label = tkinter.Label(recipient_window, text='Recipient').pack(side=tkinter.LEFT)
  input_text = tkinter.StringVar()
  recipient_entry = tkinter.Entry(recipient_window, textvariable=input_text)
  recipient_entry.pack(side=tkinter.RIGHT)
  recipient_entry.bind('<Return>', get_input)

def show_history():
  pass

"""
  initialize_message_history()

  Open a GUI window to allow user to open a message history with a specific
  reicipient.
"""
def initialize_message_history(root):
  select_history_window = tkinter.Toplevel(root)

  # Callback function to get the recipient's username and open the chat window
  def get_input(_):
    recipient = input_text.get()
    
    chats[recipient].chat()
    recipient_window.destroy()

  # Load menu to select recipients with whom to chat
  label = tkinter.Label(recipient_window, text='Recipient').pack(side=tkinter.LEFT)
  input_text = tkinter.StringVar()
  recipient_entry = tkinter.Entry(recipient_window, textvariable=input_text)
  recipient_entry.pack(side=tkinter.RIGHT)
  recipient_entry.bind('<Return>', get_input)

"""
  listen()

  Listen for incoming data from the server. Parse incoming data and dispatch the
  incoming user messages accordingly.
"""
def listen(client_socket, root):
  while True:
    data = client_socket.receive()

    headers, payload = client_socket.parse_incoming(data)
    event = headers['event']

    # Message from recipient
    if event == 'incoming':
      recipient = headers['from']
      if recipient not in chats: chats[recipient] = Chat(client_socket, root, recipient)
      chats[recipient].load_message(recipient, headers['type'], payload)

    # Message from server reflecting the outgoing messaging back to client
    # indicating an error
    elif event == 'outgoing' and headers['status'] == 'failure' and headers['type'] == 'server':
      recipient = headers['to']
      if recipient not in chats: chats[recipient] = Chat(client_socket, root, recipient)
      chats[recipient].load_message(recipient, headers['type'], payload)

"""
  show_messaging_menu()

  Prompt the logged in user for messaging actions.
"""
def show_chat_menu(client_socket):
  root = tkinter.Tk()

  # Style chat menu window
  root.geometry('300x100')
  root.title('{} - chat menu'.format(client_socket.get_username()))
  tkinter.Label(root, text='Logged in as: {}'.format(client_socket.get_username())).pack(fill=tkinter.X)

  # Spawn a new thread to listen for data pushes from the server
  listener = Thread(target=listen, args=(client_socket,root), daemon=True)
  listener.start()

  chat_button = tkinter.Button(root, text='Chat', command=lambda: initialize_chat(client_socket, root)).pack()
  message_history_button = tkinter.Button(root, text='Message History', command=lambda: initialize_message_history(root)).pack()
  exit_button = tkinter.Button(root, text='Exit', command=client_socket.disconnect).pack()

  root.mainloop()
