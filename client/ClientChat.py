from queue import Queue
from threading import Thread
import tkinter

chats = {}

"""
  Chat

  A wrapper to group messages in the same conversations (i.e., to the same
  recipient) powered by event-driven GUI.
"""
class Chat:
  def __init__(self, client_socket, root, recipient):
    self.client_socket = client_socket
    self.root = root
    self.username = client_socket.get_username()
    self.recipient = recipient
    self.message_queue = Queue()
    self.conversation = ''

  # Open a chat window: accept input to send as messages and update the window
  # with incoming messages
  def chat(self):
    chat_window = tkinter.Toplevel(self.root)

    # Callback to get input from user to send to recipient
    def get_input(_):
      payload = input_text.get()
      message_entry.delete(0, tkinter.END) # Clear input field
      headers = 'event: outgoing\nusername: {}\nto: {}\n\n'.format(self.username, self.recipient)
      self.client_socket.send(headers + payload)
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
  initialize_chat()

  Initialize a new chat with a recipient.
"""
def initialize_chat(client_socket, root):
  recipient_window = tkinter.Toplevel(root)

  # Callback function to get the recipient's username and open the chat window
  def get_input(_):
    recipient = input_text.get()
    if recipient not in chats:
      chats[recipient] = Chat(client_socket, root, recipient)
    chats[recipient].chat()
    recipient_window.destroy()

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
def listen(client_socket):
  while True:
    data = client_socket.receive()

    headers, payload = client_socket.parse_incoming(data)
    event = headers['event']
    recipient = headers['from']
    if event == 'incoming':
      if recipient not in chats: chats[recipient] = Chat(recipient)
      chats[recipient].load_message('{}: {}'.format(recipient, payload))

"""
  show_messaging_menu()

  Prompt the logged in user for messaging actions.
"""
def show_chat_menu(client_socket):
  # Spawn a new thread to listen for data pushes from the server
  listener = Thread(target=listen, args=(client_socket,), daemon=True)
  listener.start()

  root = tkinter.Tk()

  chat_button = tkinter.Button(root, text='Chat', command=lambda: initialize_chat(client_socket, root)).pack()
  exit_button = tkinter.Button(root, text='Exit', command=lambda: client_socket.disconnect(0)).pack()
  #initialize_chat(client_socket, root)

  root.mainloop()
