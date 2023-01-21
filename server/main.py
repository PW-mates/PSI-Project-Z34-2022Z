# Create a FTP server from scratch
import os
import threading
from ftp_server import FTPServer, FTPUser
from session import Session
from utils import get_user

def main():
    # create a FTP User if it doesn't exist
    username = 'ftp_user'
    username2 = 'ftp_user2'
    user = get_user(username)
    if (user is None):
        password = '$y$j9T$s5tx/LtsbzvLC8gJ9Mos2/$6fOlBz8DIeRvdFGmLDPof6Zsy7GaCC6y2mfPU5XWiY8'
        su_session = Session()
        try:
            su_session.create_ftp_user(username, password)
            su_session.create_ftp_user(username2, password)
            print(f'Created user {username} with password "abcd"')
        except Exception as e:
            print('Exception: ', e)
            return
        


    host = '0.0.0.0'
    port = 21
    # get full path to server.crt and server.key
    server_cert =  os.path.abspath('./certs/cert.pem')
    server_key =  os.path.abspath('./certs/key.pem')
    print('server_cert: ', server_cert)
    server = FTPServer(host, port, server_cert, server_key)
    # run the server in a separate thread
    server_tls_thread = threading.Thread(target=server.run_tls)
    server_tls_thread.start()
    server_thread = threading.Thread(target=server.run)
    server_thread.start()





if __name__ == '__main__':
    main()
