import json
from pathlib import Path
import os
from getpass import getpass
import ClientAuthentication
import ClientServerConnection
import ClientChat
import MessageHistory

def messaging(client_socket):
    ClientChat.show_chat_menu(client_socket)
    return True

def accountDelete(client_socket):
    choice = input("Are you sure you want to delete your account? Y/N: ")
    if(choice.lower() == 'y'):
        #TODO: actrual delete account
        password = getpass()
        flag = ClientAuthentication.deleteAccount(client_socket,password)
        if(flag == 0):
            print("Account Deleted")
            input('Press any key to continue...')
            return False
        else:
            print("Something went wrong")
            input('Press any key to continue...')
            return True
    else:
        os.system("clear")
        return True

def logout(client_socket):
    ClientAuthentication.logout(client_socket)
    return False

def register(client_socket):
    #UI for register, will login automatically after
    flag = True
    while flag:
        print("Register Menu")
        username = input("Username: ")
        if(username == "!back"):
            return False
        password = getpass()
        os.system("clear")
        passStrength = ClientAuthentication.passwordCheck(password)
        if(passStrength[0] == False):
            print(passStrength[1] + '\n')
            continue
        flag = ClientAuthentication.register(client_socket,username,password)
        if(flag == 1):
            print("Registration failed!\n")
        else:
            print("Registration succeeded!\n")
            ClientAuthentication.login(client_socket,username,password)
            create_user_config(username, password)
            return True

def login(client_socket):
    #UI for login
    flag = True
    while flag:
        print("Login Menu")
        username = input("Username: ")
        if(username == "!back"):
            return False
        password = getpass()
        os.system("clear")
        flag = ClientAuthentication.login(client_socket,username,password)
        if(flag == 1):
            print("Login failed!\n")
        else:
            print("Login succeeded!\n")
            create_user_config(username, password)
            return True

def getUI(UIName,savedData):
    root = savedData[UIName]
    values = list(root.values())
    choice = -1
    msg = ""

    while True:
        os.system("clear")
        print(UIName)
        for key in root:
            print(key)

        print("\n" + msg)
        choice = input("Enter your choice: ")
        if not choice.isnumeric():
            msg = "Please input integer"
        elif int(choice) <= 0 or int(choice) > len(values):
            msg = "Invalid input"
        else:
            os.system("clear")
            return values[int(choice)-1]

def create_user_config(username, password):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    user_dir = Path(root_dir + '/{}'.format(username))
    user_config_path = Path(root_dir + '/{}/config.json'.format(username))

    # Validate username input; enforce child path of ./client/
    if not user_config_path.is_relative_to(root_dir):
        return None

    # Create the yser directory for username if it doesn't exist
    try:
        os.makedirs(user_dir)
    except FileExistsError:
        pass

    # Create a new config file if it doesn't exist
    if os.path.exists(user_config_path):
        return None

    mhe = MessageHistory.MessageHistoryEncryption()
    private_pem, public_pem = mhe.generate_private_key(password)

    data = {}
    data['private_pem'] = private_pem.decode('utf-8')
    data['public_pem'] = public_pem.decode('utf-8')

    config_fd = open(user_config_path, 'w')
    json.dump(data, config_fd, indent=2)
    config_fd.close()
