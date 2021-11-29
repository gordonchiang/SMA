
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
