from queue import Queue
from threading import Thread
import tkinter
import tkinter.filedialog
from PIL import Image, ImageTk
import io

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
    self.message_queue = Queue() # (username, type, message)
    self.conversation = ''
    self.conversation_picture_history = Queue()

  # Open a chat window: accept input to send as messages and update the window
  # with incoming messages
  def chat(self):
    chat_window = tkinter.Toplevel(self.root)

    # Callback to get input from user to send to recipient
    def get_input(_):
      payload = input_text.get()
      message_entry.delete(0, tkinter.END) # Clear input field

      # Build and send message to recipient
      headers = 'event: outgoing\nusername: {}\nto: {}\ntype: text\n\n'.format(self.username, self.recipient)
      self.client_socket.send(headers + payload)

      # Display the message in the chat window
      self.load_message(self.username, 'text', payload)

    # Callback to update the chat window with messages every second
    def display_conversation():
      while not self.message_queue.empty():
        try:
          # Get new messages to load into the chat window
          sender, message_type, message = self.message_queue.get_nowait()

          # Simply print text messages
          if message_type == 'text':
            conversation.insert(tkinter.END, '{}: {}\n'.format(sender, message))

          # Convert images back to image format and display them
          elif message_type == 'image':
            conversation.insert(tkinter.END, '{}:\n'.format(sender))

            # Convert image from string to bytes
            image_data = bytes(message, encoding='latin1')
  
            # Open the image from memory to avoid saving to disk
            image = Image.open(io.BytesIO(image_data))
            img = ImageTk.PhotoImage(image)

            # Prevent image from being garbage-collected; persist in chat window
            self.conversation_picture_history.put(img) 

            # Create image on the GUI
            conversation.image_create(tkinter.END, image=img)
            conversation.insert(tkinter.END, '\n')

          self.save_history(sender, message_type, message)
            
        except Exception as e:
          continue

      chat_window.after(500, display_conversation) # Update the window

    # Callback to select an image to send to the recipient
    def get_image():
      image_path = tkinter.filedialog.askopenfilename(initialdir='/', title='Select image', filetypes=(('gif files','*.gif'),))
      if image_path:
        fd = open(image_path, 'rb')
        payload = fd.read()
        fd.close()

        payload = payload.decode(encoding='latin1') # Encode bytes to string for transmission

        headers = 'event: outgoing\nusername: {}\nto: {}\ntype: image\n\n'.format(self.username, self.recipient)
        self.client_socket.send(headers + payload)
        self.load_message(self.username, 'image', payload)

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

    # Request image from the user
    image_entry = tkinter.Button(chat_window, text='Image', command=get_image)
    image_entry.pack()

  # Save history of chat between self.username and self.recipient
  def save_history(self, sender, message_type, message):
    pass # TODO

  # Queue messages so they get loaded into the chat window in order
  def load_message(self, sender, message_type, message):
    self.message_queue.put_nowait((sender, message_type, message))


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
def listen(client_socket):
  while True:
    data = client_socket.receive()

    headers, payload = client_socket.parse_incoming(data)
    event = headers['event']
    recipient = headers['from']
    if event == 'incoming':
      if recipient not in chats: chats[recipient] = Chat(recipient)
      chats[recipient].load_message(recipient, headers['type'], payload)

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
  exit_button = tkinter.Button(root, text='Exit', command=client_socket.disconnect).pack()

  root.mainloop()
