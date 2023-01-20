# Create a FTP server from scratch

import os
import threading
from ftp_server import FTPServer, FTPUser

def main():
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


    # user = get_user('ftp_user')
    # if (user is None):
    #     raise Exception('User not found')
    # su_session = Session(user, "abcd")

    # # su_session.create_ftp_user('ftp_user3', 'password')
    # print('su_session.authenticated: ', su_session.authenticated)


if __name__ == '__main__':
    main()
