class Chat:
    """
      Chat

      A wrapper to group messages in the same conversations (i.e., to the same
      recipient) and to power the GUI.
    """

    def __init__(self, partner):
        self.username = username
        self.partner = partner
        self.message_queue = Queue()
        self.conversation = ''


    # Open a chat window: accept input to send as messages and update the window
    # with incoming messages
    def chat(self):
        chat_window = tkinter.Toplevel(root)

        # Callback to get input from user to send to partner
        def get_input(_):
            payload = input_text.get()
            message_entry.delete(0, tkinter.END) # Clear input field
            headers = 'event: outgoing\nusername: {}\nto: {}\n\n'.format(self.username, self.partner)
            client_socket.send(headers + payload)
            self.load_message('{}: {}'.format(self.username, payload))

        # Callback to update the chat window with messages every second
        def display_conversation():
            while not self.message_queue.empty():
                try:
                    text = self.message_queue.get_nowait()
                    conversation.insert(tkinter.END, text)
                except:
                    continue

            chat_window.after(1000, display_conversation)

        # Create a Text widget to display the messages
        conversation = tkinter.Text(chat_window)
        conversation.insert(tkinter.END, self.conversation)
        conversation.update()
        conversation.pack()

        # Periodically update the messages
        display_conversation()

        # Request input from the user
        label = tkinter.Label(chat_window, text='Message').pack()
        input_text = tkinter.StringVar()
        message_entry = tkinter.Entry(chat_window, textvariable=input_text)
        message_entry.pack()
        message_entry.bind('<Return>', get_input)

    # Queue messages so they get loaded into the chat window in order
    def load_message(self, message):
        self.message_queue.put_nowait(message + '\n')

"""
  chat()

  Initialize a new chat with a partner.
"""
def chat(root):
    partner_window = tkinter.Toplevel(root)

    # Request the partner's username and open the chat window
    def get_input(_):
        partner = input_text.get()
        if partner not in chats:
            chats[partner] = Chat(partner)
        chats[partner].chat()
        partner_window.destroy()

        label = tkinter.Label(partner_window, text='Partner' ).pack()
        input_text = tkinter.StringVar()
        partner_entry = tkinter.Entry(partner_window, textvariable=input_text)
        partner_entry.pack()
        partner_entry.bind('<Return>', get_input)

"""
  show_messaging_menu()

  Prompt the logged in user for messaging actions.
"""
def show_messaging_menu():
  # Spawn a new thread to listen for data pushes from the server
    listener = Thread(target=listen, daemon=True)
    listener.start()

    global root
    root = tkinter.Tk()

    chat_button = tkinter.Button(root, text='Chat', command=lambda: chat(root)).pack()
    exit_button = tkinter.Button(root, text='Exit', command=lambda: client_socket.disconnect(SUCCESS)).pack()

    root.mainloop()
