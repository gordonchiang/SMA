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
    return 0
  else:
    return 1

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
    return 0
  else:
    return 1

def logout(client_socket):
    client_socket.disconnect()

def deleteAccount(client_socket, pw):
    if not pw: return 1

    message = 'event: delete\nusername: {}\npassword: {}\n\n'.format(client_socket.get_username(), pw)
    client_socket.send(message)
    response = client_socket.receive()
    headers, _ = client_socket.parse_incoming(response)
    if headers['event'] == 'delete' and headers['status'] == 'success':
      client_socket.disconnect()
      return 0
    else:
      return 1

def passwordCheck(password):
    import re
    if(' ' in password):
        return (False,"Password must not include space")
    if(len(password) < 8):
        return (False,"Password must be longer than 8 characters")
    if(not re.search("[a-z]",password)):
        return (False,"Password contain both uppercase and lowercase letters")
    if(not re.search("[A-Z]",password)):
        return (False,"Password contain both uppercase and lowercase letters")
    if(not re.search("[0-9]",password)):
        return (False,"Password contain both letters and numbers")
    return (True,"Valid password")
