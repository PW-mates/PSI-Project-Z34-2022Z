import socket

# Initialze socket
# TCP_IP = "127.0.0.1"
TCP_IP = "103.130.212.186"
TCP_PORT = 21
global TCP_PORT_PASV, TCP_PORT_ACTIVE, PASV_MODE, ACTIVE_MODE
TCP_PORT_PASV = None
TCP_PORT_ACTIVE = None
PASV_MODE = True
ACTIVE_MODE = False
BUFFER_SIZE = 1024
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def listen_data():
    global TCP_PORT_PASV
    global TCP_PORT_ACTIVE
    port = None
    if TCP_PORT_PASV is not None:
        port = TCP_PORT_PASV
    if TCP_PORT_ACTIVE is not None:
        port = TCP_PORT_ACTIVE
    if port is None:
        return None, None
    client_socket_tmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket_tmp.connect((TCP_IP, port))
    data = client_socket_tmp.recv(1024).decode()
    client_socket_tmp.close()
    # print("\n" + response)
    response = client_socket.recv(1024).decode()
    # print("\n" + response)
    TCP_PORT_PASV = None
    TCP_PORT_ACTIVE = None
    return data, response

def send_data(data):
    global TCP_PORT_PASV
    global TCP_PORT_ACTIVE
    port = None
    if TCP_PORT_PASV is not None:
        port = TCP_PORT_PASV
    if TCP_PORT_ACTIVE is not None:
        port = TCP_PORT_ACTIVE
    if port is None:
        return None, None
    client_socket_tmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket_tmp.connect((TCP_IP, port))
    client_socket_tmp.send(data)
    client_socket_tmp.close()
    response = client_socket.recv(1024).decode()
    TCP_PORT_PASV = None
    TCP_PORT_ACTIVE = None
    return response

# Send command to server
def send_command(command):
    client_socket.send(command.encode())
    response = client_socket.recv(1024).decode()
    print("\n" + response)
    return response

# Command: CONNECT
def connect():
    client_socket.connect((TCP_IP, TCP_PORT))
    response = client_socket.recv(1024).decode()
    print("\n" + response)
    print("\nConnected to server")
    print("\nPassive mode activated by default")


def doElse(command):
    command = command + '\r\n'
    send_command(command)


# Command: USER
def user(username):
    command = 'USER {}\r\n'.format(username)
    send_command(command)

# Command: PASS
def passwd(password):
    command = 'PASS {}\r\n'.format(password)
    send_command(command)

# Command: PWD
def pwd():
    command = 'PWD\r\n'
    send_command(command)

# Command: LIST
def list():
    if PASV_MODE:
        pasv()
    command = 'LIST\r\n'
    send_command(command)
    data, response = listen_data()
    print(data)
    print(response)

# Command: PWD
def pwd():
    command = 'PWD\r\n'
    send_command(command)

# Command: CWD
def cwd(directory):
    command = 'CWD {}\r\n'.format(directory)
    send_command(command)

# Command: QUIT
def quit():
    command = 'QUIT\r\n'
    send_command(command)
    client_socket.close()
    print("\nConnection closed")
    return

# Command: UPLD
def upld(client_socket, filepath):
    with open(filepath, 'rb') as f:
        command = 'UPLD {}\r\n'.format(filepath)
        client_socket.send(command.encode())
        # Wait for the server to accept the upload
        response = client_socket.recv(1024).decode()
        if response.startswith('150'):
            # Send the file contents to the server
            client_socket.sendall(f.read())
        # Wait for the server to finish processing the upload
        response = client_socket.recv(1024).decode()
        if response.startswith('226'):
            print("File uploaded successfully")
        else:
            print("Error uploading file: " + response)

# Command: RETR
def retr(filepath):
    if PASV_MODE:
        pasv()

    command = 'RETR {}\r\n'.format(filepath)
    first_response = send_command(command)
    data, response = listen_data()
    if first_response.startswith('150'):
        # Create a new file to store the contents
        with open(filepath, 'w') as f:
            f.write(data)
        # Wait for the server to finish processing the download
        if response.startswith('226'):
            print("File downloaded successfully")
        else:
            print("Error downloading file: " + response)

# Command: STOR
def stor(filepath):
    if PASV_MODE:
        pasv()

    command = 'STOR {}\r\n'.format(filepath)
    first_response = send_command(command)
    if first_response.startswith('150'):
        # Create a new file to store the contents
        with open(filepath, 'r') as f:
            data = f.read()
        # Send the file contents to the server
        response = send_data(data.encode())
        # Wait for the server to finish processing the upload
        if response.startswith('226'):
            print("File uploaded successfully")
        else:
            print("Error uploading file: " + response)

# Command: PASV
def pasv():
    global TCP_PORT_PASV
    command = 'PASV\r\n'
    client_socket.send(command.encode())
    response = client_socket.recv(1024).decode()

    print(response)

    val = response.split('(')[-1].split(')')[0].split(',')
    # address = '.'.join(val[:4])
    port = int(val[4]) * 256 + int(val[5])
    TCP_PORT_PASV = port
    # return address, port

# Function to switch between active and passive mode
def passive_mode():
    global ACTIVE_MODE, PASV_MODE
    PASV_MODE = True
    ACTIVE_MODE = False
    print("\nPassive mode activated")

def active_mode():
    global ACTIVE_MODE, PASV_MODE
    ACTIVE_MODE = True
    PASV_MODE = False
    print("\nActive mode activated")

# Command: HELP
def help():
    print("\nCommands:")
    print("CONNECT - Connect to server")
    print("USER <username> - Send username")
    print("PASS <password> - Send password")
    print("PWD - Print working directory")
    print("LIST - List files in current directory")
    print("CWD <directory> - Change working directory")
    print("UPLD <filepath> - Upload file to server")
    print("GET <filepath> - Download file from server")
    print("QUIT - Close connection")
    print("HELP - Print this message")


print("Welcome to FTP client")
print("Type HELP for a list of commands")
while True:
    command = input("\n> ").split()
    if command[0] == "CONNECT":
        connect()
    elif command[0] == "USER":
        user(command[1])
    elif command[0] == "PASS":
        passwd(command[1])
    elif command[0] == "PWD":
        pwd()
    elif command[0] == "LIST":
        list()
    elif command[0] == "CWD":
        cwd(command[1])
    elif command[0] == "UPLD":
        upld(command[1])
    elif command[0] == "RETR":
        retr(command[1])
    elif command[0] == "STOR":
        stor(command[1])
    elif command[0] == "PASV":
        passive_mode()
    elif command[0] == "ACTIVE":
        active_mode()
    elif command[0] == "QUIT":
        quit()
        break
    elif command[0] == "HELP":
        help()
    else:
        doElse(' '.join(command))
