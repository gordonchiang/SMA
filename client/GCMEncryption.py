# References
# https://cryptography.io/en/latest/hazmat/primitives/asymmetric/dh/
# https://cryptography.io/en/latest/hazmat/primitives/aead/

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

NONCE_SIZE = 16
p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF
g = 2
params_numbers = dh.DHParameterNumbers(p,g)
parameters = params_numbers.parameters()

# Associated data for GCM authentication
AD = b'GCMAuthenticationData'

class DH_Keys:
	#
	# Initialize private and public keys
	# Note that Ephemeral Diffie-Hellman is used here to ensure perfect forward secrecy
	#
	def __init__(self):
		self.priv_key = parameters.generate_private_key()
		self.public_key = self.priv_key.public_key()

	#
	# Generate shared key
	#
	def gen_shared_key(self, peer_key):
		shared_key = self.priv_key.exchange(peer_key)
		derived_key = HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'handshake data',).derive(shared_key)
		return derived_key

#
# Symmetric cryptography using Diffie-Hellman key (key must be 128, 192, or 256 bits)
# Message must be in bytes for aesgcm to encrypt
# Nonce is never reused, size is 16 bytes
# Nonce is stored with the cipher since it does not need to be secret
#
def encrypt_message(message, key):
	aesgcm = AESGCM(key)
	message_in_bytes = str.encode(message)
	nonce = os.urandom(NONCE_SIZE)
	cipher = aesgcm.encrypt(nonce, message_in_bytes, AD)
	cipher = nonce + cipher
	return cipher

#
# Symmetric cryptography using Diffie-Hellman key (must be 128, 192, or 256 bits)
# First 16 bytes used as nonce, rest are the cipher
#
def decrypt_message(cipher, key):
	aesgcm = AESGCM(key)
	try:
		plaintext = aesgcm.decrypt(cipher[0:16], cipher[16:], AD)
		return plaintext.decode()
	except Exception as e:
		return "MESSAGE NOT AUTHENTICATED"

#
# Used for debug purposes
#
def main():
	# A would be the sender, B would be the recipient
	A = DH_Keys()
	B = DH_Keys()

	# Generate shared keys
	A_shared_key = A.gen_shared_key(B.public_key)
	B_shared_key = B.gen_shared_key(A.public_key)

	input_msg = input("Input: ")
	print("Shared DH key is:",A_shared_key)
	cipher = encrypt_message(input_msg, A_shared_key)
	
	decrypted_message = decrypt_message(cipher, A_shared_key)
	print(decrypted_message)

if __name__ == "__main__":
	main()