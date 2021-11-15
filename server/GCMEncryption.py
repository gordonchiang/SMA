import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import sqlite3

USERS_DATABASE = 'users.db'
NONCE_SIZE = 16

# Associated data for authentication
AD = b'GCMAuthenticationData'

def save_history(sender, recipient, message, sender_hashed_pwd):
	encrypted_msg = encrypt_message(message, sender_hashed_pwd)

	try:
		conn = sqlite3.connect(USERS_DATABASE)
		cursor = conn.cursor()
		cursor.execute('INSERT INTO chat_history(sender, recipient, hashed_msg) VALUES(?,?,?)', (sender, recipient, encrypted_msg))
		conn.commit()

	except Exception as e:
		print(e)
		conn.close()

def show_history(sender, recipient, sender_hashed_pwd):

	try:
		conn = sqlite3.connect(USERS_DATABASE)
		cursor = conn.cursor()
		cursor.execute('SELECT * FROM chat_history WHERE sender = "Logan"')
		rows = cursor.fetchall()
		for row in rows:
			print("ID: ", row[0])
			print("Sender: ", row[1])
			print("Recipient: ", row[2])
			decrypted_msg = decrypt_message(row[3], sender_hashed_pwd)
			print("Message: ", decrypted_msg.decode())




	except Exception as e:
		print(e)
		conn.close()


def encrypt_message(message, sender_hashed_pwd):
	# Symmetric cryptography using hashed sender password as key (must be 128, 192, or 256 bits)
	sender_key = sender_hashed_pwd.encode()
	aesgcm = AESGCM(sender_key)

	# Message must be in bytes for aesgcm to encrypt
	message_in_bytes = str.encode(message)

	nonce = os.urandom(NONCE_SIZE)
	cipher = aesgcm.encrypt(nonce, message_in_bytes, AD)

	# Nonce is stored with the cipher since it does not need to be secret
	cipher = nonce + cipher
	return cipher

def decrypt_message(cipher, sender_hashed_pwd):
	# Symmetric cryptography using hashed sender password as key (must be 128, 192, or 256 bits)
	sender_key = sender_hashed_pwd.encode()
	aesgcm = AESGCM(sender_key)
	
	# First 16 bytes used as nonce, rest are the cipher
	plaintext = aesgcm.decrypt(cipher[0:16], cipher[16:], AD)
	return plaintext

def main():
	# TODO: Make the encryption work with messages coming from the client
	# TODO: Save encrypted messages in database/textfile
	input_msg = input("Enter message to encrypt: ")
	save_history("Logan", "Lagan", input_msg, "passwordpassword")
	show_history("Logan", "Lagan", "passwordpassword")
	encrypted_msg = encrypt_message(input_msg, "passwordpassword")
	try:
		decrypted_msg = decrypt_message(encrypted_msg, "passwordpassword")
		#print("Your decrypted message is: " + decrypted_msg.decode())
	except Exception as e:
		print("Message not authenticated.")

if __name__ == "__main__":
	main()