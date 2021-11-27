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

    self.history = None

    print(self.recipient, self.key)

    history_available = self.__open_history()
    if history_available is False:
      # TODO: show error popup
      self.__show_error()
      pass
    else:
      self.__show_history()
      pass

  def __open_history(self):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    history_path = Path(root_dir + '/{}/{}'.format(self.username, self.recipient))

    # Validate username and recipient input; enforce child path of ./client/
    if not history_path.is_relative_to(root_dir):
      self.history = None
      return False

    try:
      fd = open(dir_path, 'r')
    except:
      self.history = None
      return False
    else:
      self.history = fd.read()
      fd.close()
      return True

  def __show_history(self):
    if self.history is None:
      # Show error popup
      return

    history_window = tkinter.Toplevel(self.root)

    # Style chat window
    history_window.title('{} - message history with {}'.format(self.username, self.recipient))
    tkinter.Label(history_window, text='Message history with: {}'.format(self.recipient)).pack(fill=tkinter.X)

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
