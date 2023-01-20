from utils import get_user, demote, login
import subprocess
import os

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
    
    def devote(self):
        return demote(self.user.uid, self.user.gid)

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
    
    def run_command(self, command):
        if not self.authenticated:
            return
        output, error = self.run(command)
        if output:
            print('output: ', output)
        if error:
            print('error: ', error)
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
