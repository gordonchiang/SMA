import base64
import io
from pathlib import Path
from PIL import Image, ImageTk
from queue import Queue
from re import match, DOTALL
import os
import tkinter
import tkinter.messagebox

class Reader:
  def __init__(self, root, username, recipient, private_key):
    self.username = username
    self.root = root
    self.recipient = recipient
    self.private_key = private_key

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
    while history:
      message_match = match('^(?P<sender>.*?)\n(?P<type>.*?)\n(?P<length>.*?)\n.*$', history, flags=DOTALL)
      sender = message_match['sender']
      message_type = message_match['type']
      length = message_match['length']
      message_length = int(length)
      control_length = len(sender) + len(message_type) + len(length) + 3 # 3 '\n'

      message = history[control_length:control_length+message_length]

      decoded_history.put_nowait((sender, message_type, message))

      history = history[control_length+message_length:]

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

    # Delete the file if it exists
    if os.path.exists(history_path): os.remove(history_path)

    tkinter.messagebox.showinfo('Success', 'History with {} has been deleted!'.format(self.recipient))

    history_window.destroy()

class Writer:
  def __init__(self, username, recipient, public_key):
    self.username = username
    self.recipient = recipient
    self.public_key = public_key

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
    history_fd = self.__open_history()
    history_fd.write('{}\n{}\n{}\n{}'.format(sender, message_type, len(message), message))
    history_fd.close()
