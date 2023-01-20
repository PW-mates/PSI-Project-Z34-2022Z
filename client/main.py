import random
import socket

# Initialze socket
# TCP_IP = "127.0.0.1"
TCP_IP = "103.130.212.186"
TCP_PORT = 21
global TCP_PORT_PASV, TCP_PORT_ACTIVE, PASV_MODE, ACTIVE_MODE, TYPE_MODE, BUFFER_SIZE
TCP_PORT_PASV = None
TCP_PORT_ACTIVE = None
PASV_MODE = True
ACTIVE_MODE = False
BUFFER_SIZE = 1024
TYPE_MODE = 'I'
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def listen_data():
    global TCP_PORT_PASV
    global TCP_PORT_ACTIVE
    port = None
    if PASV_MODE:
        port = TCP_PORT_PASV
    elif ACTIVE_MODE:
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
    if PASV_MODE:
        port = TCP_PORT_PASV
    elif ACTIVE_MODE:
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
    print("\nBinary mode activated by default")


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
    else:
        port()
    command = 'LIST\r\n'
    first_response = send_command(command)
    if first_response.startswith('150'):
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

# Command: RETR
def retr(filepath):
    if PASV_MODE:
        pasv()
    else:
        port()

    command = 'RETR {}\r\n'.format(filepath)
    first_response = send_command(command)
    if first_response.startswith('150'):
        data, response = listen_data()
        # Create a new file to store the contents
        mode = 'w'
        if TYPE_MODE == 'I':
            mode = 'wb'
        try:
            if TYPE_MODE == "I":
                data = data.encode()
            with open(filepath, mode) as f:
                f.write(data)
        except:
            print("Error writing file with mode: " + mode)
        # Wait for the server to finish processing the download
        if response.startswith('226'):
            print("File downloaded successfully")
        else:
            print("Error downloading file: " + response)

# Command: STOR
def stor(filepath):
    # Create a new file to store the contents
    mode = 'r'
    if TYPE_MODE == 'I':
        mode = 'rb'
    data = None
    try:
        with open(filepath, mode) as f:
            data = f.read()
    # catch file not found error, read error and return
    except FileNotFoundError:
        print("File not found")
        return
    except:
        print("Error reading file with mode: " + mode)
        return

    if PASV_MODE:
        pasv()
    else:
        port()

    command = 'STOR {}\r\n'.format(filepath)
    first_response = send_command(command)
    if first_response.startswith('150'):
        # Send the file contents to the server
        if TYPE_MODE == 'A':
            data = data.encode()
        response = send_data(data)
        # Wait for the server to finish processing the upload
        if response.startswith('226'):
            print("File uploaded successfully")
        else:
            print("Error uploading file: " + response)

# Command: DELE
def dele(filepath):
    command = 'DELE {}\r\n'.format(filepath)
    send_command(command)

# Command: MKD
def mkd(directory):
    command = 'MKD {}\r\n'.format(directory)
    send_command(command)

# Command: RMD
def rmd(directory):
    command = 'RMD {}\r\n'.format(directory)
    send_command(command)

# Command: RNFR and RNTO
def ren(old_name, new_name):
    command = 'RNFR {}\r\n'.format(old_name)
    first_response = send_command(command)
    if first_response.startswith('350'):
        command = 'RNTO {}\r\n'.format(new_name)
        send_command(command)

# Command: TYPE
def type(type):
    global TYPE_MODE
    if type not in ['A', 'I']:
        print("Invalid type")
        return
    if type == 'A':
        TYPE_MODE = 'A'
    else:
        TYPE_MODE = 'I'
    command = 'TYPE {}\r\n'.format(type)
    send_command(command)

# Command: PORT
def port():
    global TCP_PORT_ACTIVE, PASV_MODE, ACTIVE_MODE
    PASV_MODE = False
    ACTIVE_MODE = True
    TCP_PORT_ACTIVE = random.randint(1024, 65535)
    ip = socket.gethostbyname(socket.gethostname())
    ip = ip.split('.')
    ip = ','.join(ip)
    # Convert the port from int to 2 port data
    port = TCP_PORT_ACTIVE // 256, TCP_PORT_ACTIVE % 256
    # Convert the port data to string
    port = [str(i) for i in port]
    port = ','.join(port)
    command = 'PORT {},{}\r\n'.format(ip, port)
    send_command(command)

# Command: PASV
def pasv():
    global TCP_PORT_PASV
    command = 'PASV\r\n'
    client_socket.send(command.encode())
    response = client_socket.recv(1024).decode()

    print(response)

    val = response.split('(')[-1].split(')')[0].split(',')
    port = int(val[4]) * 256 + int(val[5])
    TCP_PORT_PASV = port

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
    print("RETR <filename> - Download file")
    print("STOR <filename> - Upload file")
    print("DELE <filename> - Delete file")
    print("MKD <directory> - Create directory")
    print("RMD <directory> - Remove directory")
    print("REN <old_name> <new_name> - Rename file")
    print("TYPE <type> - Set transfer type")
    print("PASV - Switch to passive mode")
    print("PORT - Switch to active mode")
    print("QUIT - Close connection")
    print("HELP - Print this message")


print("Welcome to FTP client")
print("Type HELP for a list of commands")
while True:
    try:
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
        elif command[0] == "RETR":
            retr(command[1])
        elif command[0] == "STOR":
            stor(command[1])
        elif command[0] == "PASV":
            passive_mode()
        elif command[0] == "PORT":
            active_mode()
        elif command[0] == "DELE":
            dele(command[1])
        elif command[0] == "MKD":
            mkd(command[1])
        elif command[0] == "RMD":
            rmd(command[1])
        elif command[0] == "REN":
            ren(command[1], command[2])
        elif command[0] == "TYPE":
            type(command[1])
        elif command[0] == "QUIT":
            quit()
            break
        elif command[0] == "HELP":
            help()
        else:
            print("Invalid command. Type HELP for a list of commands")
            # doElse(' '.join(command))
    except Exception as e:
        print(e)
