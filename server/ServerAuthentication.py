import sqlite3
import os
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

"""
  generate_kdf()

  Runs Scrypt to generate a KeyDerivationInstance with static parameters.
"""
def generate_kdf(salt):
  return Scrypt(
    salt=salt,
    length=32,
    n=2**14,
    r=8,
    p=1,
  )

"""
  verify_password()

  Verifies a user-inputted password with the saved password hash. Raises an
  exception if verification fails to fail client authentication.
"""
def verify_password(plaintext, hash, salt):
  generate_kdf(salt).verify(plaintext.encode(), hash)

"""
  register_new_user()

  Register a new user account in the SQL database.
"""
def register_new_user(client_socket, db, username, password):
  try:
    # Generate a salt and hash the password
    salt = os.urandom(16)
    kdf = generate_kdf(salt)
    password_hash = kdf.derive(password.encode()) # Convert password string to bytearray

    # Verify if the saved password works
    verify_password(password, password_hash, salt)

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Insert new user credentials and save the database
    cursor.execute('''
      INSERT INTO users(username, password_hash, salt)
      VALUES(?,?,?)
    ''', (username, password_hash, salt))
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

    # Query for the hashed password and salt
    cursor.execute('''
      SELECT password_hash, salt FROM users
      WHERE username = ?
    ''', (username,))
    password_hash, salt = cursor.fetchone()

    # Verify the password
    verify_password(password, password_hash, salt)

  # If any error arises, fail authentication and notify the client
  except:
    conn.close()
    client_socket.send('event: login\nstatus: failure\n\n'.encode())
    return None

  else:
    # No record was returned, fail authentication and notify the client
    if not password_hash or not salt:
      conn.close()
      client_socket.send('event: login\nstatus: failure\n\n'.encode())
      return None

    # Notify the client of successful authentication
    else:
      conn.close()
      connection.set_username(username)
      client_socket.send('event: login\nstatus: success\n\n'.encode())
      return username

"""
  delete_user()

  Delete a user account from the SQL database.
"""
def delete_user(client_socket, db, username, password):
  try:
    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Query for the hashed password and salt
    cursor.execute('''
      SELECT password_hash, salt FROM users
      WHERE username = ?
    ''', (username,))
    password_hash, salt = cursor.fetchone()

    # Verify the password
    verify_password(password, password_hash, salt)

    # Delete user information from the database and save the database
    cursor.execute('''
      DELETE FROM users
      WHERE username = ?
    ''', (username,))
    conn.commit()

    # Verify deletion
    cursor.execute('''
      SELECT username FROM users
      WHERE username = ?
    ''', (username,))
    row = cursor.fetchone()

  # If any error arises, fail deletion and notify client
  except:
    conn.close()
    client_socket.send('event: delete\nstatus: failure\n\n'.encode())

  else:
    # Deletion was successful
    if row is None:
      conn.close()
      client_socket.send('event: delete\nstatus: success\n\n'.encode())

    # Username still exists in database, failed deletion
    else:
      conn.close()
      client_socket.send('event: delete\nstatus: failure\n\n'.encode())
