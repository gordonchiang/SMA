import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_SIZE = 128
NONCE_SIZE = 12
AD = b'GCMAuthenticationTag'  # Associated data for authentication

class GCM_Encryption:
	def __init__(self):
		# Initialize key and nonce so the message can be decrypted afterwards
		self.key = AESGCM.generate_key(KEY_SIZE)
		self.aesgcm = AESGCM(self.key)
		self.nonce = os.urandom(NONCE_SIZE)

	def encrypt_message(self, message):
		# Message must be in bytes for aesgcm to encrypt
		message_in_bytes = str.encode(message)
		cipher = self.aesgcm.encrypt(self.nonce, message_in_bytes, AD)
		return cipher

	def decrypt_message(self, message):
		plaintext = self.aesgcm.decrypt(self.nonce, message, AD)
		return plaintext

def main():
	# TODO: Make the encryption work with messages coming from the client
	# TODO: Save encrypted messages in database/textfile
	GCM = GCM_Encryption()
	input_msg = input("Enter message to encrypt: ")
	encrypted_msg = GCM.encrypt_message(input_msg)
	print(type(encrypted_msg))
	try:
		decrypted_msg = GCM.decrypt_message(encrypted_msg)
		print("Your decrypted message is: " + decrypted_msg.decode())
	except Exception as e:
		print("Message not authenticated.")

if __name__ == "__main__":
	main()