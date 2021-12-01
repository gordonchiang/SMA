import base64
import io
from PIL import Image, ImageTk
from queue import Queue
import tkinter
import tkinter.filedialog
from GCMEncryption import *

import MessageHistory

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
    self.history = MessageHistory.Writer(self.username, self.recipient)

    self.key_buffer = {}
    self.message_buffer = ""
    self.message_type_buffer = ""

  """
    chat()

    Open a chat window. Accept input to send as messages and update the window
    with incoming messages. Save messags to message history.
  """
  def chat(self):
    chat_window = tkinter.Toplevel(self.root)

    # Style chat window
    chat_window.title('{} - chatting with {}'.format(self.username, self.recipient))
    tkinter.Label(chat_window, text='Chatting with: {}'.format(self.recipient)).pack(fill=tkinter.X)

    def save_key_buffer(key_type, key):
      self.key_buffer[key_type] = key

    def get_key_buffer(key_type):
      return self.key_buffer[key_type]

    def get_message_type():
      return self.message_type_buffer

    # Send public key to recipient of message or back to sender of message
    # key_type here is either peer_keyA (sender public key) or peer_keyB (recipient public key)
    def send_public_key(recipient, key_type):
      keys = DH_Keys() # Generate keys
      self.key_buffer[priv] = keys.get_priv_key() # Store private key to buffer to encrypt message later

      payload = keys.get_public_key() # Set payload to public key to send to B
      headers = 'event: outgoing\nusername: {}\nto: {}\ntype: {}\n\n'.format(self.username, recipient, key_type)
      self.client_socket.send(headers + payload)

    # Send encrypted message to recipient of message
    # payload is cipher of message
    def send_encrypted_msg(recipient, shared_key, msg_type):
      payload = encrypt_message(self.message_buffer, shared_key)
      headers = 'event: outgoing\nusername: {}\nto: {}\ntype: {}\n\n'.format(self.username, recipient, msg_type)
      self.message_buffer = ""
      self.client_socket.send(headers + payload)

    # Callback to get input from user to send to recipient
    def get_input(_):
      payload = input_text.get()
      message_entry.delete(0, tkinter.END) # Clear input field
      self.message_buffer = payload # Save message in buffer to encrypt later
      self.message_type_buffer = 'text_enc'

      # Send public key from A to B
      send_public_key(self.recipient, 'peer_keyA')

      # Display the message in the chat window
      self.load_message(self.username, 'text', payload)

    # Callback to select an image to send to the recipient
    def get_image():
      image_path = tkinter.filedialog.askopenfilename(initialdir='~', title='Select image', filetypes=(('gif files','*.gif'),))
      if image_path:
        fd = open(image_path, 'rb')
        payload = base64.b64encode(fd.read()).decode('utf-8')
        fd.close()
        self.message_buffer = payload # Save image in buffer to encrypt later
        self.message_type_buffer = 'image_enc'

        # Send public key from A to B
        send_public_key(self.recipient, 'peer_keyA')

        # Display the image in the chat window
        self.load_message(self.username, 'image', payload)

    # Callback to update the chat window with messages periodically
    def display_conversation():
      while not self.message_queue.empty():
        try:
          # Get new messages to load into the chat window
          sender, message_type, message = self.message_queue.get_nowait()

          # Simply print text messages
          if message_type == 'text':
            conversation.insert(tkinter.END, '{}: {}\n'.format(sender, message))
            self.history.save_to_history(sender, message_type, message) # Save to history

          # Convert images back to image format and display them
          elif message_type == 'image':
            conversation.insert(tkinter.END, '{}:\n'.format(sender))

            # Convert image from string to bytes
            image_data = base64.b64decode(message.encode('utf-8'))
  
            # Open the image from memory to avoid saving to disk
            image = Image.open(io.BytesIO(image_data))
            img = ImageTk.PhotoImage(image)

            # Prevent image from being garbage-collected; persist in chat window
            self.conversation_picture_history.put(img)

            # Create image on the GUI
            conversation.image_create(tkinter.END, image=img)
            conversation.insert(tkinter.END, '\n')

            self.history.save_to_history(sender, message_type, message) # Save to history

          # Server message
          else:
            conversation.insert(tkinter.END, '{}\n'.format(message))

          if not message_type == 'server': self.save_history(sender, message_type, message)
            
        except:
          continue

      chat_window.after(500, display_conversation) # Update the GUI window

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
    image_entry = tkinter.Button(chat_window, text='Send Image', command=get_image)
    image_entry.pack()

  # Queue messages so they get loaded into the chat window in order
  # If message is coming from sender, it needs to be decrypted
  # If message is being printed on the console by the sender, it does not need to be decrypted
  def load_message(self, sender, message_type, message):
    # If message is encrypted and is a text message
    if(message_type == 'text_enc'):
      shared_key = gen_shared_key(self.key_buffer['priv'], self.key_buffer['public'])
      decrypted_message = decrypt_message(message, shared_key)
      self.message_queue.put_nowait((sender, 'text', decrypted_message))

    # If message is encrypted and is an image
    elif(message_type == 'image_enc'):
      shared_key = gen_shared_key(self.key_buffer['priv'], self.key_buffer['public'])
      decrypted_message = decrypt_message(message, shared_key)
      self.message_queue.put_nowait((sender, 'image', decrypted_message))

    # If message is not encrypted (just printing text/image on own console)
    else:
      self.message_queue.put_nowait((sender, message_type, message))
