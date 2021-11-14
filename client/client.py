#!/usr/bin/env python3

from socket import socket, AF_INET, SOCK_STREAM
import ssl
import sys
import ClientAuthentication
import ClientChat
import ClientServerConnection
import CliUI

import json
import os

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
    sock = ctx.wrap_socket(pre_sock, server_hostname=server_address[0])
    sock.connect(server_address)

    return ClientServerConnection.ClientServerConnection(sock)

  # Failed to connect to server, exit
  except:
    sys.stderr.write('Unable to connect to the server\n')
    sys.exit(1)

def main():
    SERVER_ADDRESS = ('localhost', 9000)
    with open("./client/config.json") as jfile:
        savedData = json.load(jfile)

    programFlag = True
    while programFlag:
        client_socket = connect((savedData["ServerInfo"]["ServerIP"],savedData["ServerInfo"]["ServerPort"]))
        loginFlag = False
        while not loginFlag: #While not logged in
            func = CliUI.getUI("LogIn Menu",savedData)
            loginFlag = eval("CliUI." + func + "(client_socket)")

        input('Press any key to continue...')

        mainFlag = True
        while mainFlag:
            func = CliUI.getUI("MainMenu",savedData)
            mainFlag = eval("CliUI." + func + "(client_socket)")
            print(programFlag)

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    sys.exit(0)
