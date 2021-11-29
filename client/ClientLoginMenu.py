import tkinter
import tkinter.messagebox

class LoginMenu:
  

def login_prompt(login_menu, client_socket):
  login_box = tkinter.Toplevel(login_menu)

  # Callback function to login to the server with username and password
  def login(_ = None):
    username = username_text.get()
    password = password_text.get()

    if username and password:
      login_success = ClientAuthentication.login(client_socket, username, password)
      if login_success is True:
        ClientChat.show_main_menu(login_menu, client_socket)
        login_menu.withdraw()
        login_box.destroy()
      else:
        tkinter.messagebox.showinfo('Error', 'Login failed!')
        login_box.destroy()

  # Load menu to login
  # Get the username
  username_label = tkinter.Label(login_box, text='Username').grid(row=0, column=0)
  username_text = tkinter.StringVar()
  username_entry = tkinter.Entry(login_box, textvariable=username_text)
  username_entry.grid(row=0, column=1)

  # Get the password
  password_label = tkinter.Label(login_box, text='Password').grid(row=1, column=0)
  password_text = tkinter.StringVar()
  password_entry = tkinter.Entry(login_box, show='*', textvariable=password_text)
  password_entry.grid(row=1, column=1)
  password_entry.bind('<Return>', login)

  submit_button = tkinter.Button(login_box, text='Login', command=login).grid(row=3, column=1)

def register_prompt(login_menu, client_socket):
  register_box = tkinter.Toplevel(login_menu)

  # Callback function to register a new account with the server
  def register(_ = None):
    username = username_text.get()
    password = password_text.get()
    repeat_password = repeat_password_text.get()

    if username and password and repeat_password:
      if not password == repeat_password:
        tkinter.messagebox.showinfo('Error', 'Passwords do not match!')
        register_box.destroy()
      else:
        register_success = ClientAuthentication.register(client_socket, username, password)
        if register_success is True:
          tkinter.messagebox.showinfo('Success', 'Your account {} has been registered!'.format(username))
          register_box.destroy()
        else:
          tkinter.messagebox.showinfo('Error', 'Registration failed!')
          register_box.destroy()

  # Load menu to register
  # Get the username
  username_label = tkinter.Label(register_box, text='Username').grid(row=0, column=0)
  username_text = tkinter.StringVar()
  username_entry = tkinter.Entry(register_box, textvariable=username_text)
  username_entry.grid(row=0, column=1)

  # Get the password
  password_label = tkinter.Label(register_box, text='Password').grid(row=1, column=0)
  password_text = tkinter.StringVar()
  password_entry = tkinter.Entry(register_box, show='*', textvariable=password_text)
  password_entry.grid(row=1, column=1)

  repeat_password_label = tkinter.Label(register_box, text='Repeat Password').grid(row=2, column=0)
  repeat_password_text = tkinter.StringVar()
  repeat_password_entry = tkinter.Entry(register_box, show='*', textvariable=repeat_password_text)
  repeat_password_entry.grid(row=2, column=1)
  repeat_password_entry.bind('<Return>', register)

  submit_button = tkinter.Button(register_box, text='Register', command=register).grid(row=3, column=1)
