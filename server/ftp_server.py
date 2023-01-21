import os
import random
import sys
import socket
import threading
import subprocess
from utils import get_user
from session import Session
import ssl

class FTPUser:
    def __init__(self, username, password, permissions, home_dir):
        self.username = username
        self.password = password
        self.permissions = permissions
        self.home_dir = home_dir

class FTPServer:
    def __init__(self, host, port, server_cert, server_key):
        self.host = host
        self.port = port
        self.server_cert = server_cert
        self.server_key = server_key

        # Explicit FTP (Port 21)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(5)
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) 
        self.ssl_context.load_cert_chain(certfile=self.server_cert, keyfile=self.server_key)

        # Implicit TLS (Port 990)
        self.sock_tls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_tls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_tls = ssl.wrap_socket(self.sock_tls, server_side=True, certfile=self.server_cert, keyfile=self.server_key, do_handshake_on_connect=True)
        self.sock_tls.bind((host, 990))
        self.sock_tls.listen(5)
        print('FTP server started on {}:{}'.format(host, port))
        print('TLS server started on {}:{}'.format(host, 990))
        
        # self.sock.settimeout(0.1)
        self.clients = {}
        self.commands = {
            'auth': self.cmd_auth,
            'user': self.cmd_user,
            'pass': self.cmd_pass,
            'port': self.cmd_port,
            'list': self.cmd_ls,
            'syst': self.cmd_syst,
            'pbsz': self.cmd_pbsz,
            'prot': self.cmd_prot,
            'pwd': self.cmd_pwd,
            'type': self.cmd_type,
            'pasv': self.cmd_pasv,
            'cwd': self.cmd_cwd,
            'opts': self.cmd_opts,
            'retr': self.cmd_retr,
            'stor': self.cmd_stor,
            'mkd': self.cmd_mkd,
            'rmd': self.cmd_rmd,
            'rnfr': self.cmd_rnfr,
            'rnto': self.cmd_rnto,
            'dele': self.cmd_dele,
            'site': self.cmd_site,
        }
        self.current_dir = os.getcwd()
        self.lock = threading.Lock()

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
            self.clients[client.getpeername()] = {'client': client, 'address': address, 'auth_mode': 'plaintext', 'transfer_type': 'I'}
            threading.Thread(target=self.handle_client, args=(client.getpeername(),), daemon=True).start()

    def run_tls(self):
        while True:
            # Accept FTP connection and ask for authentication
            try:
                client, address = self.sock_tls.accept()
                print('TLS connection from: ', address)
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                print('Server stopped')
                self.sock_tls.close()
                sys.exit(0)
            self.clients[client.getpeername()] = {'client': client, 'address': address, 'auth_mode': 'TLS', 'transfer_type': 'I'}
            print('Client peername: ', client.getpeername())
            threading.Thread(target=self.handle_client, args=(client.getpeername(),), daemon=True).start()

    def handle_client(self, name):
        client = self.clients[name]['client']
        client_name = client.getpeername()
        client.send('220 Welcome to FTP server\n'.encode('utf-8'))
        try:
            while True:
                # Refresh client if wrapped in TLS
                client = self.clients[name]['client']
                try:
                    data = client.recv(1024)
                except socket.timeout:
                    continue
                if not data:
                    break
                data = data.decode('utf-8')
                print (f'Client {client.getpeername()} sent: {data}')
                cmd = data.split(' ')[0].lower().strip()
                print(f'Client {client.getpeername()} sent command: {cmd} {data[len(cmd)+1:]}')
                if cmd in self.commands:
                    self.commands[cmd](client, data)
                elif cmd == 'quit':
                    client.send('221 Goodbye\n'.encode('utf-8'))
                    self.close_client(client)
                else:
                    print(f'Invalid command: {cmd}')
                    client.send('500 Invalid command\n'.encode('utf-8'))
        except Exception as e:
            print(f'Client {client_name} error: {e}')
        finally:
            if client:
                if self.clients[client.getpeername()]['auth_mode'] == 'TLS':
                    client = client.unwrap()
                client.close()
                print(f'Client {client_name} disconnected')
    
    def close_client(self, client):
        client.send('221 Goodbye\n'.encode('utf-8'))
        del self.clients[client.getpeername()]
        raise Exception('Client disconnected')
    
    def close_data_connection(self, client):
        data_socket = self.clients[client.getpeername()]['data_socket']
        if (data_socket):
            if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                data_socket = data_socket.unwrap()
            data_socket.close()
            self.clients[client.getpeername()]['data_socket'] = None
            print('Data connection closed')
        
    
    def cmd_auth(self, client, data):
        print('Setting authentication mode...')
        mode = data.split(' ')[1].strip()
        self.clients[client.getpeername()]['auth_mode'] = mode
        if (mode != 'TLS' and mode != 'SSL'):
            print('Invalid authentication mode')
            client.send('500 Invalid authentication mode\n'.encode('utf-8'))
            self.close_client(client)
        
        if (mode == 'TLS'):
            print('Starting TLS server...')
            client.send('234 Authentication mode set to TLS\n'.encode('utf-8'))
            client = self.ssl_context.wrap_socket(client, server_side=True)
            print('TLS server started')
            self.clients[client.getpeername()]['client'] = client
        elif (mode == 'SSL'):
            # not supported
            client.send('500 SSL not supported\n'.encode('utf-8'))
            self.close_client(client)

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
        user = get_user(username)
        self.clients[client.getpeername()]['user'] = user
        if (user == None):
            client.send('530 Login incorrect\n'.encode('utf-8'))
            self.close_client(client)
        try:
            self.clients[client.getpeername()]['session'] = Session(user, password)
        except Exception as e:
            client.send(f'530 {e}\n'.encode('utf-8'))
            print('Error creating session: ', e)
            self.close_client(client)
        client.send('230 Login successful\n'.encode('utf-8'))
        print('Login successful')

    
    def cmd_port(self, client, data):
        print('Setting port...')
        self.clients[client.getpeername()]['mode'] = 'active'
        split_data = data.split(' ')[1].split(',')
        ip = '.'.join(split_data[:4])
        port = int(split_data[4]) * 256 + int(split_data[5])
        print(f'IP: {ip}, Port: {port}')
        self.clients[client.getpeername()]['socket'] = {
            'ip': ip,
            'port': port
        }
        client.send('200 PORT command successful\n'.encode('utf-8'))

    def cmd_ls(self, client, data):
        print('Listing files...')
        session = self.clients[client.getpeername()]['session']
        try:
            output, error = session.run_command('ls -la')
            if error:
                client.send(f'550 {error}\n'.encode('utf-8'))
                return
            client.send('150 Here comes the directory listing.\n'.encode('utf-8'))
            
            # remove first line of output
            output = output.replace('\r', '')
            output = output.split('\n')[1:]
            output = '\n'.join(output)
            print(output)
            if (self.clients[client.getpeername()]['mode'] == 'passive'):
                print('Waiting for connection...')
                try:
                    conn, addr = self.clients[client.getpeername()]['data_socket'].accept()
                    print("Current auth mode: ", self.clients[client.getpeername()]['auth_mode'])
                    if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                        
                        conn = self.ssl_context.wrap_socket(conn, server_side=True)
                    print('Connection accepted: ', conn.getpeername())
                
                    conn.send(output.encode('utf-8'))
                    if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                        conn = conn.unwrap()
                finally:
                    print("terminating connection")
                    conn.shutdown(socket.SHUT_RDWR)
                    conn.close()
                    self.close_data_connection(client)
            elif (self.clients[client.getpeername()]['mode'] == 'active'):
                try:
                    try:
                        context = ssl.SSLContext()
                        context.load_default_certs()
                        ip = self.clients[client.getpeername()]['socket']['ip']
                        port = self.clients[client.getpeername()]['socket']['port']
                        print(f'Connecting to {ip}:{port}')
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        # sock.bind(('', 20))
                        sock.settimeout(5)
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            sock = context.wrap_socket(sock, do_handshake_on_connect=True)
                        sock.connect((ip, port))
                        print('Connected to client: ', sock.getpeername())
                        sock.send(output.encode('utf-8'))
                    except Exception as e:
                        print('Error sending data: ', str(e))
                        return
                    finally:
                        print("terminating connection")
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            sock = sock.unwrap()
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()
                except Exception as e:
                    print('Error connecting to client: ', str(e))
                    return
            else:
                client.send('425 Use PORT or PASV first.\n'.encode('utf-8'))
                return
            client.send('226 Directory send OK.\n'.encode('utf-8'))
            print('Done listing files')
        except Exception as e:
            print('Error listing files: ', str(e))
            client.send(f'550 Error listing files {str(e)}\n'.encode('utf-8'))
    
    def cmd_syst(self, client, data):
        print('Sending system info...')
        client.send('215 UNIX Type: L8\n'.encode('utf-8'))

    def cmd_pbsz(self, client, data):
        print('Setting buffer size...')
        self.clients[client.getpeername()]['buffer_size'] = int(data.split(' ')[1].strip())
        client.send('200 PBSZ command successful\n'.encode('utf-8'))
    
    def cmd_prot(self, client, data):
        print('Setting protection level...')
        self.clients[client.getpeername()]['protection_level'] = data.split(' ')[1].strip()
        client.send('200 PROT command successful\n'.encode('utf-8'))
    
    def cmd_pwd(self, client, data):
        print('Sending current directory...')
        session = self.clients[client.getpeername()]['session']
        client.send(f'257 "{session.cwd}"\n'.encode('utf-8'))

    def cmd_type(self, client, data):
        print('Setting transfer type...')
        self.clients[client.getpeername()]['transfer_type'] = data.split(' ')[1].strip()
        client.send('200 TYPE command successful\n'.encode('utf-8'))
    
    def cmd_pasv(self, client, data):
        print('Setting passive mode...')
        self.clients[client.getpeername()]['mode'] = 'passive'
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # random socket port between 65000 and 65535
        port = random.randint(65000, 65535)
        sock.bind((self.host, port))
        sock.settimeout(5)
        sock.listen(1)
        self.clients[client.getpeername()]['data_socket'] = sock
        ip, port = sock.getsockname()
        print(f'IP: {ip}, Port: {port}')
        client.send(f'227 Entering Passive Mode ({ip.replace(".", ",")},{port // 256},{port % 256})\n'.encode('utf-8'))
    
    def cmd_cwd(self, client, data):
        print('Changing directory...')
        session = self.clients[client.getpeername()]['session']
        try:
            cwd = session.cwd
            session.change_dir(data.split(' ')[1].strip())
            if (os.path.exists(session.cwd) and os.path.isdir(session.cwd)):
                client.send('250 CWD command successful\n'.encode('utf-8'))
            else:
                session.cwd = cwd
                client.send('550 Error changing directory\n'.encode('utf-8'))
        except Exception as e:
            print('Error changing directory: ', str(e))
            client.send('550 Error changing directory\n'.encode('utf-8'))
    
    def cmd_opts(self, client, data):
        print('Setting options...')
        opts_name = data.split(' ')[1].strip()
        opts_value = data.split(' ')[2].strip()
        self.clients[client.getpeername()]['options'][opts_name] = opts_value
        client.send('200 OPTS command successful\n'.encode('utf-8'))
    
    def cmd_retr(self, client, data):
        print('Retrieving file...')
        session = self.clients[client.getpeername()]['session']
        file_path = data.split(' ')[1].strip()
        file_path = os.path.join(session.cwd, file_path)
        print(f'File path: {file_path}')
        client.send('150 Opening data connection for file transfer.\n'.encode('utf-8'))
        try:
            # check file transfer mode
            transfer_type = self.clients[client.getpeername()]['transfer_type']
            open_mode = 'r'
            if (transfer_type == 'I'):
                open_mode = 'rb'
            with open(file_path, open_mode) as f:
                file_data = f.read()
                if (self.clients[client.getpeername()]['mode'] == 'passive'):
                    try:
                        conn, addr = self.clients[client.getpeername()]['data_socket'].accept()
                        print('Connection accepted: ', conn.getpeername())
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            conn = self.ssl_context.wrap_socket(conn, server_side=True)
                        
                        print("Transfer type: ", transfer_type)
                        if (transfer_type == 'A'):
                            print("Converting file data to bytes...")
                            try:
                                file_data = bytes(file_data, 'utf-8')
                            except Exception as e:
                                print('Error converting file data to bytes: ', str(e))
                                client.send('550 File is not support to transfer in ASCII mode\n'.encode('utf-8'))
                                return
                        conn.send(file_data)
                    finally:
                        print("terminating connection")
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            conn = conn.unwrap()
                        conn.shutdown(socket.SHUT_RDWR)
                        conn.close()
                        self.close_data_connection(client)
                elif (self.clients[client.getpeername()]['mode'] == 'active'):
                    try:
                        context = ssl.SSLContext()
                        # context.load_default_certs()
                        ip = self.clients[client.getpeername()]['socket']['ip']
                        port = self.clients[client.getpeername()]['socket']['port']
                        print(f'Connecting to {ip}:{port}')
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        # sock.bind(('', 20))
                        sock.settimeout(5)
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            sock = context.wrap_socket(sock)
                        sock.connect((ip, port))
                        if (transfer_type == 'A'):
                            print("Converting file data to bytes...")
                            try:
                                file_data = bytes(file_data, 'utf-8')
                            except Exception as e:
                                print('Error converting file data to bytes: ', str(e))
                                client.send('550 File is not support to transfer in ASCII mode\n'.encode('utf-8'))
                                return
                        sock.send(file_data)
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            sock = sock.unwrap()
                        client.send('226 Transfer complete.\n'.encode('utf-8'))
                    except Exception as e:
                        print('Error sending data: ', str(e))
                        return
                    finally:
                        print("terminating connection")
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()

                    # method not supported
                    # client.send('502 Method not supported\n'.encode('utf-8'))
                else:
                    client.send('425 Use PORT or PASV first.\n'.encode('utf-8'))
                    return
                client.send('226 Transfer complete.\n'.encode('utf-8'))
                print('Done sending file')
        except socket.timeout:
            print('Connection timed out')
            return
        except Exception as e:
            print('Error sending file: ', str(e))
            client.send('550 Error sending file\n'.encode('utf-8'))
    
    def cmd_stor(self, client, data):
        print('Storing file...')
        session = self.clients[client.getpeername()]['session']
        file_path = data.split(' ')[1].strip()
        file_path = os.path.join(session.cwd, file_path)
        print(f'File path: {file_path}')
        client.send('150 Opening data connection.\n'.encode('utf-8'))
        try:
            # check transfer type first
            transfer_type = self.clients[client.getpeername()]['transfer_type']
            open_mode = 'wb'
            if (transfer_type == 'A'):
                open_mode = 'w'
            with open(file_path, open_mode) as f:
                if (self.clients[client.getpeername()]['mode'] == 'passive'):
                    try:
                        conn, addr = self.clients[client.getpeername()]['data_socket'].accept()
                        print('Connection accepted: ', conn.getpeername())
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            conn = self.ssl_context.wrap_socket(conn, server_side=True)
                        while True:
                            data = conn.recv(1024)
                            if not data:
                                break
                            if (transfer_type == 'A'):
                                try:
                                    data = data.decode('ascii')
                                    f.write(data)
                                except Exception as e:
                                    print('Error decoding file data: ', str(e))
                                    client.send('550 File is not support in ascii mode\n'.encode('utf-8'))
                                    return
                            f.write(data)
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            conn = conn.unwrap()
                    finally:
                        print("terminating connection")
                        conn.shutdown(socket.SHUT_RDWR)
                        conn.close()
                        self.close_data_connection(client)
                elif (self.clients[client.getpeername()]['mode'] == 'active'):
                    try:
                        context = ssl.SSLContext()
                        # context.load_default_certs()
                        ip = self.clients[client.getpeername()]['socket']['ip']
                        port = self.clients[client.getpeername()]['socket']['port']
                        print(f'Connecting to {ip}:{port}')
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        # sock.bind(('', 20))
                        sock.settimeout(5)
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            sock = context.wrap_socket(sock)
                        sock.connect((ip, port))
                        while True:
                            data = sock.recv(1024)
                            if not data:
                                break
                            if (transfer_type == 'A'):
                                try:
                                    data = data.decode('ascii')
                                except Exception as e:
                                    print('Error decoding file data: ', str(e))
                                    client.send('550 File is not support in ascii mode\n'.encode('utf-8'))
                                    return
                            f.write(data)
                        if (self.clients[client.getpeername()]['auth_mode'] == 'TLS'):
                            sock = sock.unwrap()
                    except Exception as e:
                        print('Error receiving data: ', str(e))
                        return
                    finally:
                        print("terminating connection")
                        sock.shutdown(socket.SHUT_RDWR)
                        sock.close()

                    # method not supported
                    # client.send('502 Method not supported\n'.encode('utf-8'))
                else:
                    client.send('425 Use PORT or PASV first.\n'.encode('utf-8'))
                    return
                
                client.send('226 Transfer complete.\n'.encode('utf-8'))
                os.chown(file_path, self.clients[client.getpeername()]['session'].user.uid, self.clients[client.getpeername()]['session'].user.gid)

                print('Done storing file')
        except socket.timeout:
            print('Connection timed out')
            return
        except Exception as e:
            print('Error storing file: ', str(e))
            client.send('550 Error storing file\n'.encode('utf-8'))
    
    def cmd_mkd(self, client, data):
        print('Creating directory...')
        session = self.clients[client.getpeername()]['session']
        dir_path = data.split(' ')[1].strip()
        dir_path = os.path.join(session.cwd, dir_path)
        print(f'Directory path: {dir_path}')
        try:
            os.mkdir(dir_path)
            client.send('257 Directory created.\n'.encode('utf-8'))
            print('Done creating directory')
        except Exception as e:
            print('Error creating directory: ', str(e))
            client.send('550 Error creating directory\n'.encode('utf-8'))
    
    def cmd_rmd(self, client, data):
        print('Removing directory...')
        session = self.clients[client.getpeername()]['session']
        dir_path = data.split(' ')[1].strip()
        dir_path = os.path.join(session.cwd, dir_path)
        print(f'Directory path: {dir_path}')
        try:
            os.rmdir(dir_path)
            client.send('250 Directory removed.\n'.encode('utf-8'))
            print('Done removing directory')
        except Exception as e:
            print('Error removing directory: ', str(e))
            client.send('550 Error removing directory\n'.encode('utf-8'))

    def cmd_rnfr(self, client, data):
        print('Renaming file...')
        session = self.clients[client.getpeername()]['session']
        file_path = data.split(' ')[1].strip()
        file_path = os.path.join(session.cwd, file_path)
        print(f'File path: {file_path}')
        try:
            if os.path.isfile(file_path):
                self.clients[client.getpeername()]['rename'] = file_path
                client.send('350 File exists, ready for destination name.\n'.encode('utf-8'))
            elif os.path.isdir(file_path):
                self.clients[client.getpeername()]['rename'] = file_path
                client.send('350 Directory exists, ready for destination name.\n'.encode('utf-8'))
            else:
                client.send('550 File or directory does not exist.\n'.encode('utf-8'))
        except Exception as e:
            print('Error renaming file: ', str(e))
            client.send('550 Error renaming file\n'.encode('utf-8'))
    
    def cmd_rnto(self, client, data):
        print('Renaming file...')
        session = self.clients[client.getpeername()]['session']
        file_path = data.split(' ')[1].strip()
        file_path = os.path.join(session.cwd, file_path)
        print(f'File path: {file_path}')
        if not self.clients[client.getpeername()]['rename']:
            client.send('503 Bad sequence of commands.\n'.encode('utf-8'))
            return
        if not file_path:
            client.send('501 Syntax error in parameters or arguments.\n'.encode('utf-8'))
            return
        if file_path == self.clients[client.getpeername()]['rename']:
            client.send('553 Requested action not taken. File name not allowed.\n'.encode('utf-8'))
            return
        if os.path.isfile(file_path) or os.path.isdir(file_path):
            client.send('553 Requested action not taken. File name not allowed.\n'.encode('utf-8'))
            return
        try:
            if os.path.isfile(self.clients[client.getpeername()]['rename']):
                os.rename(self.clients[client.getpeername()]['rename'], file_path)
                client.send('250 File renamed.\n'.encode('utf-8'))
            elif os.path.isdir(self.clients[client.getpeername()]['rename']):
                os.rename(self.clients[client.getpeername()]['rename'], file_path)
                client.send('250 Directory renamed.\n'.encode('utf-8'))
            else:
                client.send('550 File or directory does not exist.\n'.encode('utf-8'))
        except Exception as e:
            print('Error renaming file: ', str(e))
            client.send('550 Error renaming file\n'.encode('utf-8'))
    
    def cmd_dele(self, client, data):
        print('Deleting file...')
        session = self.clients[client.getpeername()]['session']
        file_path = data.split(' ')[1].strip()
        file_path = os.path.join(session.cwd, file_path)
        print(f'File path: {file_path}')
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                client.send('250 File deleted.\n'.encode('utf-8'))
            else:
                client.send('550 File does not exist.\n'.encode('utf-8'))
        except Exception as e:
            print('Error deleting file: ', str(e))
            client.send('550 Error deleting file\n'.encode('utf-8'))
                
    def cmd_site(self, client, data):
        print('Executing SITE command...')
        session = self.clients[client.getpeername()]['session']
        cmd = data[data.find(' ')+1:].strip()
        cmd = cmd.split(' ')
        cmd[0] = cmd[0].lower()
        cmd = ' '.join(cmd)
        try:
            output, error = session.run_command(cmd)
            if error:
                client.send('550 Error executing SITE command\n'.encode('utf-8'))
            else:
                client.send('200 SITE command executed.\n'.encode('utf-8'))
        except Exception as e:
            print('Error executing SITE command: ', str(e))
            client.send('550 Error executing SITE command\n'.encode('utf-8'))