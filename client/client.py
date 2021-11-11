#!/usr/bin/env python3

from socket import socket, AF_INET, SOCK_STREAM
import ssl
import sys
from ClientAuthentication import *
from ClientChat import *
from ClientServerConnection import *

SERVER_ADDRESS = ('localhost', 9000)

"""
  connect()

  Try to connect to the configured server. If connection is unsuccessful, exit.
"""
def connect(server_address):
  # Connect to the server
  try:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations('certificate.crt')
    pre_sock = socket(AF_INET, SOCK_STREAM)
    sock = ctx.wrap_socket(pre_sock, server_hostname=SERVER_ADDRESS[0])
    sock.connect(server_address)

    return ClientServerConnection(sock)

  # Failed to connect to server, exit
  except:
    sys.stderr.write('Unable to connect to the server\n')
    sys.exit(1)

def main():
  client_socket = connect(SERVER_ADDRESS)
  show_main_menu(client_socket)
  show_chat_menu(client_socket)
  sys.exit(0)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    sys.exit(0)
