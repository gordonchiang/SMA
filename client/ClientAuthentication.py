"""
  register()

  Accept user-inputted username and password and attempt to create a new account
  on the server with these credentials.
"""
def register(client_socket):
  user = input('Username: ')
  pw = input('Password (insecure!): ')
  message = 'event: register\nusername: {}\npassword: {}\n\n'.format(user, pw)
  client_socket.send(message)

  response = client_socket.receive()

  headers, _ = client_socket.parse_incoming(response)

  if headers['event'] == 'register' and headers['status'] == 'success':
    print('Registration succeeded!\n')
    return 0

  else:
    print('Registration failed!\n')
    return 1

"""
  login()

  Accept user-inputted username and password and attempt to login to the server
  with these credentials.
"""
def login(client_socket):
  user = input('Username: ')
  pw = input('Password (insecure!): ')
  message = 'event: login\nusername: {}\npassword: {}\n\n'.format(user, pw)
  client_socket.send(message)

  response = client_socket.receive()

  headers, _ = client_socket.parse_incoming(response)

  if headers['event'] == 'login' and headers['status'] == 'success':
    client_socket.set_username(user)
    print('Login succeeded!\n')
    return 0

  else:
    print('Login failed!\n')
    return 1

"""
  show_auth_menu()

  Ask the user to login to an existing account or register a new account. Once
  a user logs in successfully, messaging features are unlocked.
"""
def show_auth_menu(client_socket):
  while True:
    # Display available options
    print('1. Enter `1` to login to an existing account')
    print('2. Enter `2` to register a new account')

    # Request user input
    action = input('What would you like to do? ')

    # Error checking on user input
    if not action.isdecimal(): continue
    action = int(action)

    # Login to an existing account
    if action == 1:
      login_status = login(client_socket)
      if login_status == 0: return 0 # Proceed to next state

    # Register a new account
    elif action == 2:
      register(client_socket)
