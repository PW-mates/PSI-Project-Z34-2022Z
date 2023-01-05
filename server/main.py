# Create a FTP server from scratch

import os
import sys
import time
import socket
import threading
import struct
import subprocess

class FTPUser:
    def __init__(self, username, password, permissions, home_dir):
        self.username = username
        self.password = password
        self.permissions = permissions
        self.home_dir = home_dir


class FTPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(5)
        self.sock.settimeout(0.1)
        self.clients = {}
        self.users = {};
        self.load_users()
        self.commands = {
            'user': self.cmd_user,
            'pass': self.cmd_pass,
            'port': self.cmd_port,
            'list': self.cmd_ls,
            # 'cd': self.cmd_cd,
            # 'get': self.cmd_get,
            # 'put': self.cmd_put,
            # 'pwd': self.cmd_pwd,
            # 'mkdir': self.cmd_mkdir,
            # 'rmdir': self.cmd_rmdir,
            # 'rm': self.cmd_rm,
            # 'exit': self.cmd_exit,
        }
        self.current_dir = os.getcwd()
        self.lock = threading.Lock()
    
    def load_users(self):
        with open('users.txt', 'r') as f:
            for line in f:
                username, password, permissions, home_dir = line.split(';')
                self.users[username] = FTPUser(username, password, permissions, home_dir)

    def run(self):
        while True:
            # Accept FTP connection and ask for authentication
            try:
                client, address = self.sock.accept()
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                print('Server stopped')
                self.sock.close()
                sys.exit(0)
            self.clients[client.getpeername()] = {'client': client, 'address': address}
            threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()

    def handle_client(self, client):
        client.send('220 Welcome to FTP server\n'.encode('utf-8'))
        try:
            while True:
                try:
                    data = client.recv(1024)
                except socket.timeout:
                    continue
                if not data:
                    break
                data = data.decode('utf-8')
                cmd = data.split(' ')[0].lower().strip()
                print(f'Client {client.getpeername()} sent command: {cmd} {data[len(cmd)+1:]}')
                if cmd in self.commands:
                    self.commands[cmd](client, data)
                elif cmd == 'quit':
                    client.send('221 Goodbye\n'.encode('utf-8'))
                    self.close_client(client)
                else:
                    print(f'Invalid command: {cmd}')
                    client.send('Invalid command\n'.encode('utf-8'))
        except Exception as e:
            pass
    
    def close_client(self, client):
        client.send('221 Goodbye\n'.encode('utf-8'))
        client.close()
        del self.clients[client.getpeername()]
        raise Exception('Client disconnected')

    def cmd_user(self, client, data):
        print('Authenticating user...')
        print(f'Username: "{data.split(" ")[1].strip()}"')
        self.clients[client.getpeername()]['username'] = data.split(' ')[1].strip()
        client.send('331 Please specify the password\n'.encode('utf-8'))
    
    def cmd_pass(self, client, data):
        print('Authenticating password...')
        print(f'Password: "{data.split(" ")[1].strip()}"')
        username = self.clients[client.getpeername()]['username']
        password = data.split(' ')[1].strip()
        self.clients[client.getpeername()]['password'] = password
        if username in self.users and self.users[username].password == password:
            self.clients[client.getpeername()]['permissions'] = self.users[username].permissions
            self.clients[client.getpeername()]['current_dir'] = self.users[username].home_dir
            client.send('230 Login successful\n'.encode('utf-8'))
        else:
            client.send('530 Login incorrect\n'.encode('utf-8'))
            self.close_client(client)
    
    def cmd_port(self, client, data):
        print('Setting port...')
        split_data = data.split(' ')[1].split(',')
        ip = '.'.join(split_data[:4])
        port = int(split_data[4]) * 256 + int(split_data[5])
        print(f'IP: {ip}, Port: {port}')
        self.clients[client.getpeername()]['data_socket'] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients[client.getpeername()]['socket'] = {
            'ip': ip,
            'port': port
        }
        client.send('200 PORT command successful\n'.encode('utf-8'))

    def cmd_ls(self, client, data):
        print('Listing files...')
        files = os.listdir(self.clients[client.getpeername()]['current_dir'])
        if not files:
            client.send('550 No files in this directory\n'.encode('utf-8'))
            return
        
        client.send('150 Here comes the directory listing.\n'.encode('utf-8'))
        output = subprocess.check_output(['ls', '-l']).decode('utf-8')
        print(output)
        self.clients[client.getpeername()]['data_socket'].connect((self.clients[client.getpeername()]['socket']['ip'], self.clients[client.getpeername()]['socket']['port']))
        self.clients[client.getpeername()]['data_socket'].send(output.encode('utf-8'))
        self.clients[client.getpeername()]['data_socket'].close()
        client.send('226 Directory send OK.\n'.encode('utf-8'))
        print('Done listing files')

def main():
    host = '0.0.0.0'
    port = 21
    server = FTPServer(host, port)
    server.run()


if __name__ == '__main__':
    main()
