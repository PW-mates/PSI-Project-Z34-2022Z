import socket

# Initialze socket
TCP_IP = "127.0.0.1"
TCP_PORT = 5005
BUFFER_SIZE = 1024
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Send command to server
def send_command(command):
    client_socket.send(command.encode())
    response = client_socket.recv(1024).decode()
    print("\n" + response)

# Command: CONNECT
def connect():
    client_socket.connect((TCP_IP, TCP_PORT))
    print("\nConnected to server")

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
    command = 'LIST\r\n'
    send_command(command)

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

# Command: PASV
def pasv(client_socket):
    command = 'PASV\r\n'
    client_socket.send(command.encode())
    response = client_socket.recv(1024).decode()
    # Parse the address and port from the server's response
    address, port = response.split('(')[-1].split(')')[0].split(',')
    address = '.'.join(address)
    port = int(port[0:2]) * 256 + int(port[2:4])
    return address, port

# Function to switch between active and passive mode
def switch_mode(client_socket, mode):
    if mode == 'active':
        # Set the data port
        address = socket.gethostbyname(socket.gethostname())
        port = (5006, 5007)
        port(client_socket, address, port)
    elif mode == 'passive':
        # Enter passive mode
        pasv(client_socket)
    else:
        print("Invalid mode: " + mode)

# Command: HELP
def help():
    print("\nCommands:")
    print("CONNECT - Connect to server")
    print("USER <username> - Send username")
    print("PASS <password> - Send password")
    print("PWD - Print working directory")
    print("LIST - List files in current directory")
    print("CWD <directory> - Change working directory")
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
    elif command[0] == "RETR":
        retr(command[1])
    elif command[0] == "STOR":
        stor(command[1])
    elif command[0] == "CWD":
        cwd(command[1])
    elif command[0] == "QUIT":
        quit()
        break
    elif command[0] == "HELP":
        help()
    else:
        print("\nInvalid command")