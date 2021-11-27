import json
from pathlib import Path
import os
import tkinter
import tkinter.messagebox

class Reader:
  def __init__(self, root, username, recipient, key):
    self.username = username
    self.root = root
    self.recipient = recipient
    self.key = key

    self.history = self.__open_history()
    if self.history is None:
      self.__show_error()
    else:
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
      self.history = fd.read()
      fd.close()
      return self.history

  def __show_history(self):
    # Display an error if no history to show
    if self.history is None:
      self.__show_error()
      return

    history_window = tkinter.Toplevel(self.root)

    # Style chat window
    history_window.title('{} - message history with {}'.format(self.username, self.recipient))
    tkinter.Label(history_window, text='Message history with: {}'.format(self.recipient)).pack(fill=tkinter.X)

    # Create a Text widget to display the messages
    conversation = tkinter.Text(history_window)
    conversation.pack()
    conversation.insert(tkinter.END, self.history)

  # Display an error if unable to show history (no history, unauth, etc.)
  def __show_error(self):
    tkinter.messagebox.showinfo('Error', 'History unavailable!')

class Writer:
  def __init__(self, username, recipient, key):
    self.username = username
    self.recipient = recipient
    self.key = key

  def __create_history_dir():
    dir_path = os.path.dirname(os.path.realpath(__file__)) + self.username
    try:
      os.makedirs(dir_path)
    except FileExistsError:
      pass
