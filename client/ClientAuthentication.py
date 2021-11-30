"""
  register()

  Accept user-inputted username and password and attempt to create a new account
  on the server with these credentials.
"""
def register(client_socket, user, pw):
  if not user or not pw: return 1

  message = 'event: register\nusername: {}\npassword: {}\n\n'.format(user, pw)
  client_socket.send(message)
  response = client_socket.receive()
  headers, _ = client_socket.parse_incoming(response)
  if headers['event'] == 'register' and headers['status'] == 'success':
    return True
  else:
    return False

"""
  login()

  Accept user-inputted username and password and attempt to login to the server
  with these credentials.
"""
def login(client_socket, user, pw):
  if not user or not pw: return 1

  message = 'event: login\nusername: {}\npassword: {}\n\n'.format(user, pw)
  client_socket.send(message)
  response = client_socket.receive()
  headers, _ = client_socket.parse_incoming(response)
  if headers['event'] == 'login' and headers['status'] == 'success':
    client_socket.set_username(user)
    return True
  else:
    return False

"""
  logout()

  Logs the user out and exits.
"""
def logout(client_socket):
  client_socket.disconnect()

"""
  delete_account()

  Accept user-inputted username and password and attempt to delete the currently
  logged in aaccount with these credentials.
"""
def delete_account(client_socket, pw):
  if not pw: return 1

  message = 'event: delete\nusername: {}\npassword: {}\n\n'.format(client_socket.get_username(), pw)
  client_socket.send(message)
  response = client_socket.receive()
  headers, _ = client_socket.parse_incoming(response)
  if headers['event'] == 'delete' and headers['status'] == 'success':
    return True
  else:
    return False

"""
  validate_username_input()

  Validates username input for:
  - forbidden characters
"""
def validate_username_input(username):
  # Avoid characters that could be used to change dir
  if '.' in username:
    return False

  if '/' in username:
    return False

  if '~' in username:
    return False

  if '\n' in username: # Avoid problems with packet delimiting
    return False

  return True

"""
  validate_password_input()

  Validates password input for:
  - forbidden characters
  - length requirements
  - TO-DO: forbidden passwords (in list of common passwords)
"""
def validate_password_input(password):
  if '\n' in password: # Avoid problems with packet delimiting
    return False

  if len(password) < 8:
    return False

  # if password in list_of_common_passwords:
  #   return False

  return True
