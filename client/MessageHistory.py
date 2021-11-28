import base64
import io
import json
from pathlib import Path
from PIL import Image, ImageTk
from queue import Queue
from re import match, DOTALL
import os
import tkinter
import tkinter.messagebox

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class MessageHistoryEncryption:
  def generate_pems(self, password):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_pem = private_key.private_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PrivateFormat.PKCS8,
      encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
    )

    public_key = private_key.public_key()

    public_pem = public_key.public_bytes(
      encoding=serialization.Encoding.PEM,
      format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem

  def load_public_key(self, username):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    user_dir = Path(root_dir + '/{}'.format(username))
    user_config_path = Path(root_dir + '/{}/config.json'.format(username))

    # Validate username input; enforce child path of ./client/
    if not user_config_path.is_relative_to(root_dir):
      return None
  
    config_fd = open(user_config_path, 'r')
    data = json.load(config_fd)
    config_fd.close()
    
    public_pem = data['public_pem']

    public_key = serialization.load_pem_public_key(public_pem.encode('utf-8'))

    return public_key
    

  def load_private_key(self, username, password):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    user_dir = Path(root_dir + '/{}'.format(username))
    user_config_path = Path(root_dir + '/{}/config.json'.format(username))

    # Validate username input; enforce child path of ./client/
    if not user_config_path.is_relative_to(root_dir):
      return None
  
    config_fd = open(user_config_path, 'r')
    data = json.load(config_fd)
    config_fd.close()
    
    private_pem = data['private_pem']

    private_key = serialization.load_pem_private_key(
        private_pem.encode('utf-8'),
        password=password.encode('utf-8'),
    )

    return private_key

class Reader:
  def __init__(self, root, username, recipient, password):
    self.username = username
    self.root = root
    self.recipient = recipient

    try:
      self.private_key = MessageHistoryEncryption().load_private_key(username, password)
    except:
      self.__show_error()
      return

    self.history = self.__open_history()
    if self.history is None:
      self.__show_error()
    else:
      self.conversation_picture_history = Queue()
      self.__show_history()

  def __open_history(self):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    history_path = Path(root_dir + '/{}/{}.his'.format(self.username, self.recipient))

    # Validate username and recipient input; enforce child path of ./client/
    if not history_path.is_relative_to(root_dir):
      return None

    try:
      fd = open(history_path, 'r')
    except:
      return None
    else:
      history = fd.read()
      fd.close()
      return self.__decode_history(history)

  def __decode_history(self, history):
    decoded_history = Queue()

    # Decode history entries
    for record in [r for r in history.split('\n') if r]:
      decoded_record = base64.b64decode(record.encode('utf-8'))

      key_ciphertext = decoded_record[:256]

      message_key = self.private_key.decrypt(
        key_ciphertext,
        padding.OAEP(
          mgf=padding.MGF1(algorithm=hashes.SHA256()),
          algorithm=hashes.SHA256(),
          label=None
        )
      )

      key = message_key[:16]
      aesgcm = AESGCM(key)
      nonce = message_key[16:28]

      message_ciphertext = decoded_record[256:]

      message_plaintext = aesgcm.decrypt(nonce, message_ciphertext, None).decode('utf-8')

      record_match = match('^(?P<sender>.*?)\n(?P<type>.*?)\n(?P<message>.*)$', message_plaintext, flags=DOTALL)

      decoded_history.put_nowait((
        record_match['sender'],
        record_match['type'],
        record_match['message'],
      ))

    return decoded_history

  def __show_history(self):
    # Display an error if no history to show
    if self.history is None or self.history.empty() is True:
      self.__show_error()
      return

    history_window = tkinter.Toplevel(self.root)

    # Style chat window
    history_window.title('{} - message history with {}'.format(self.username, self.recipient))
    tkinter.Label(history_window, text='Message history with: {}'.format(self.recipient)).pack(fill=tkinter.X)

    # Create a Text widget and display the plaintext history
    conversation = tkinter.Text(history_window)
    conversation.pack()

    # Load message history into the GUI window
    self.__load_messages(conversation)

    delete_button = tkinter.Button(history_window, text='Delete History', command=lambda: self.__delete_history(history_window)).pack()

  def __load_messages(self, conversation):
    while self.history.empty() is False:
      # Get new messages to load into the history window
      sender, message_type, message = self.history.get_nowait()

      # Simply print text messages
      if message_type == 'text':
        conversation.insert(tkinter.END, '{}: {}\n'.format(sender, message))

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

  # Display an error if unable to show history (no history, unauth, etc.)
  def __show_error(self):
    tkinter.messagebox.showinfo('Error', 'History unavailable!')

  # Delete the history
  def __delete_history(self, history_window):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    history_path = Path(root_dir + '/{}/{}.his'.format(self.username, self.recipient))

    # Validate username and recipient input; enforce child path of ./client/
    if not history_path.is_relative_to(root_dir):
      return None

    # Delete the file if it exists      print(repr(record))
    if os.path.exists(history_path): os.remove(history_path)

    tkinter.messagebox.showinfo('Success', 'History with {} has been deleted!'.format(self.recipient))

    history_window.destroy()

class Writer:
  def __init__(self, username, recipient):
    self.username = username
    self.recipient = recipient
    self.public_key = MessageHistoryEncryption().load_public_key(username)

  def __open_history(self):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    history_dir = Path(root_dir + '/{}'.format(self.username))
    history_path = Path(root_dir + '/{}/{}.his'.format(self.username, self.recipient))

    # Validate username and recipient input; enforce child path of ./client/
    if not history_path.is_relative_to(root_dir):
      return None

    # Create the history directory for self.username if it doesn't exist
    try:
      os.makedirs(history_dir)
    except FileExistsError:
      pass

    # Create a new history file or open an existing one
    return open(history_path, 'a')

  def save_to_history(self, sender, message_type, message):
    plaintext = '{}\n{}\n{}'.format(sender, message_type, message)

    key = AESGCM.generate_key(bit_length=128)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)

    message_ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

    message_key = key + nonce

    key_ciphertext = self.public_key.encrypt(
      message_key,
      padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
      )
    )

    record = base64.b64encode(key_ciphertext + message_ciphertext).decode('utf-8')

    history_fd = self.__open_history()
    history_fd.write(record + '\n')
    history_fd.close()