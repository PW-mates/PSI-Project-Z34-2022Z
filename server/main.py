# Create a FTP server from scratch

import os
import sys
import time
import pwd
import socket
import threading
import struct
import subprocess
import crypt
import spwd


class User:
    def __init__(self, username, password, uid, gid, gecos, home_dir, shell):
        self.username = username
        self.password = password
        self.uid = uid
        self.gid = gid
        self.gecos = gecos
        self.home_dir = home_dir
        self.shell = shell

def get_user(username):
    try:
        pw_record = pwd.getpwnam(username)
        username = pw_record.pw_name
        home_dir = pw_record.pw_dir
        uid = pw_record.pw_uid
        gid = pw_record.pw_gid
        return User(username, None, uid, gid, None, home_dir, None)
    except:
        return None

def demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return result

def login(user, password):
    """Tries to authenticate a user.
    Returns True if the authentication succeeds, else the reason
    (string) is returned."""
    try:
        enc_pwd = spwd.getspnam(user)[1]
        if enc_pwd in ["NP", "!", "", None]:
            raise Exception("User '%s' has no password set" % user)
        if enc_pwd in ["LK", "*"]:
            raise Exception("Account is locked")
        if enc_pwd == "!!":
            raise Exception("Account has expired")
        # Encryption happens here, the hash is stripped from the
        # enc_pwd and the algorithm id and salt are used to encrypt
        # the password.
        if crypt.crypt(password, enc_pwd) == enc_pwd:
            return True
        else:
            raise Exception("Password incorrect")
    except KeyError:
        raise Exception("User '%s' does not exist" % user)


class Session:
    def __init__(self, user = None, password = None):
        # self.process = subprocess.Popen(['bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.user = user
        self.password = password
        self.authenticated = False
        self.home_dir = None
        self.is_superuser = False
        self.auth()

    def auth(self):
        if self.user:
            self.cwd = self.user.home_dir
            self.authenticated = True
            login(self.user.username, self.password)
        else:
            # keep current authenticated user
            self.user = get_user(os.getlogin().strip())
            if not self.user:
                raise Exception('User not found')
            self.cwd = self.user.home_dir
            self.authenticated = True
        print('self.authenticated: ', self.authenticated)
        if self.authenticated:
            print('Authenticated as ', self.user.username)

    def run(self, command, as_root=False, input = None):
        if not self.authenticated:
            return
        env = os.environ.copy()
        env['HOME'] = self.user.home_dir
        env['USER'] = self.user.username
        env['LOGNAME'] = self.user.username
        env['PWD'] = self.cwd
        preexec_fn = None
        if not as_root:
            preexec_fn = demote(self.user.uid, self.user.gid)
        self.process = subprocess.Popen(command.split(' '), preexec_fn=preexec_fn, cwd=self.cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if input:
            result = self.process.communicate(bytes(input, 'utf-8'))
        else:
            result = self.process.communicate()
        output = result[0].decode('utf-8').strip()
        error = result[1].decode('utf-8').strip()
        return output, error
    
    def check_run_as_root(self):
        if (self.authenticated):
            try:
                output, error = self.run('id -u', True)
            except PermissionError:
                return False # not root
            if output == '0':
                return True
            else:
                return False
    
    def create_ftp_user(self, username, password):
        if not self.check_run_as_root():
            print('Please run this command as root')
            return False
        output, error  = self.run(f'/usr/sbin/useradd -m -d /home/{username} -p {password} -s /bin/bash {username}', 'utf-8')
        if output:
            print('output: ', output)
        if error:
            print('error: ', error)
        return True

    def remove_ftp_user(self, username):
        if not self.check_run_as_root():
            print('Please run this command as root')
            return False
        result = self.process.communicate(bytes(f'/usr/sbin/userdel {username}\n', 'utf-8'))
        output = result[0].decode('utf-8').strip()
        error = result[1].decode('utf-8').strip()
        if output:
            print('output: ', output)
            return True
        if error:
            print('error: ', error)
            return False
    
    def change_dir(self, path):
        if not self.authenticated:
            return
        if path == '..':
            self.cwd = os.path.dirname(self.cwd)
        else:
            self.cwd = os.path.join(self.cwd, path)
        return self.cwd


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
    # host = '0.0.0.0'
    # port = 21
    # server = FTPServer(host, port)
    # server.run()

    user = get_user('ftp_user')
    if (user is None):
        raise Exception('User not found')
    su_session = Session(user, "abcd")

    # su_session.create_ftp_user('ftp_user3', 'password')
    print('su_session.authenticated: ', su_session.authenticated)


if __name__ == '__main__':
    main()
