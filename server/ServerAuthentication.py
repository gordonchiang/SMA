import sqlite3

"""
  register_new_user()

  Register a new user account in the SQL database.
"""
def register_new_user(client_socket, db, username, password):
  try:
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Insert new user credentials and save the database
    cursor.execute('''
      INSERT INTO users(username, password)
      VALUES(?,?)
      ''', (username, password))
    conn.commit()

  # If any error arises, fail registration and notify client
  except:
    conn.close()
    client_socket.send('event: register\nstatus: failure\n\n'.encode())

  # Notify client of successful registration
  else:
    conn.close()
    client_socket.send('event: register\nstatus: success\n\n'.encode())

"""
  delete_user()

  Delete a user account in the SQL database.
"""
def delete_user(client_socket, db, username, pw):
  try:
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Insert new user credentials and save the database
    cursor.execute('''
       DELETE FROM users
       WHERE username = ? AND password = ?
      ''', (username,pw))
    conn.commit()

  # If any error arises, fail registration and notify client
  except Exception as e:
    conn.close()
    client_socket.send('event: delete\nstatus: failure\n\n'.encode())
    print(e)
    print("fuck")

  # Notify client of successful registration
  else:
    conn.close()
    client_socket.send('event: delete\nstatus: success\n\n'.encode())

"""
  client_login()

  Authenticate a client by comparing the user-inputted username and password
  with the SQL database.
"""
def client_login(connection, db, username, password):
  client_socket = connection.get_client_socket()

  try:
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Query for the username and password
    cursor.execute('''
      SELECT username FROM users
      WHERE username = ? AND password = ?
      ''', (username, password))
    data = cursor.fetchone()

  # If any error arises, fail authentication and notify the client
  except:
    conn.close()
    client_socket.send('event: login\nstatus: failure\n\n'.encode())
    return None

  else:
    # No record was returned, fail authentication and notify the client
    if data is None:
      conn.close()
      client_socket.send('event: login\nstatus: failure\n\n'.encode())
      return None

    # Notify the client of successful authentication
    else:
      conn.close()
      connection.set_username(username)
      client_socket.send('event: login\nstatus: success\n\n'.encode())
      return username
