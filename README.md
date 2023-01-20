# PSI-Project-Z34-2022Z

### Assumptions:

- The client and server will be written in Python
- The client and server will run on 2 different containers in bigubu.ii.pw.edu.pl
- The client and server will both have access to the same set of local and remote directories

### Scope of implementation:

- The client and server should be able to handle the basic FTP commands:
```
Commands:
CONNECT - Connect to server
USER <username> - Send username
PASS <password> - Send password
AUTH TLS - Switch to TLS mode
PWD - Print working directory
LIST - List files in current directory
CWD <directory> - Change working directory
RETR <filename> - Download file
STOR <filename> - Upload file
DELE <filename> - Delete file
MKD <directory> - Create directory
RMD <directory> - Remove directory
REN <old_name> <new_name> - Rename file
TYPE <type> - Set transfer type
PASV - Switch to passive mode
PORT - Switch to active mode
ls - List files in current directory on local machine
cd <directory> - Change directory on local machine
pwd - Print working directory on local machine
mkdir <directory> - Create directory on local machine
QUIT - Close connection
HELP - Print help message
```
- The client should be able to display the contents of local and remote directories, and navigate through them
- The client should support both active and passive modes
- The client should support both binary and text modes
- The server should support concurrent connections from multiple clients
- The client and server should support a selected confidentiality mechanism (FTP)

### Use cases:

- A user wants to authenticate with the server using their username and password
- A user wants to switch between active and passive modes
- A user wants to switch between binary and text modes
- A user wants to view the contents of a local or remote directory
- A user wants to navigate to a different local or remote directory
- A user wants to transfer a file from the server to their local machine
- A user wants to transfer a file from their local machine to the server

### Architecture:

- The client and server will communicate using the FTP protocol over a TCP connection
- The client will have a user interface that allows the user to input commands and view the contents of directories
- The server will have a main process that listens for incoming connections and spawns worker processes to handle each connection
- The server will maintain a list of authenticated users and their permissions
- The client and server will both have logic to handle the various FTP commands and maintain the state of the connection (e.g. current directory, transfer mode)

### Error handling:

- The client and server should gracefully handle invalid or unexpected input from the user or the other side of the connection
- The client and server should handle errors that occur during file transfers (connection timeout, file not found)
- The client and server should handle errors that occur due to insufficient permissions or other authorization issues

### Test cases:

- Test the client's ability to authenticate with the server using a valid username and password
- Test the client's ability to switch between active and passive modes
- Test the client's ability to switch between binary and text modes
- Test the client's ability to view the contents of local and remote directories
- Test the client's ability to navigate through local and remote directories
- Test the client's ability to transfer a file from the server to the local machine
- Test the client's ability to transfer a file from the local machine to the server
- Test the server's ability to handle concurrent connections from multiple clients

### Division of work within the team:

- Truong Giang Do works on the client code, including the user interface and FTP command logic
- Minh Nguyen Cong works on the server code, including the connection handling and FTP command logic
- Daria Komarynska and Andrii Demydenko work on the error handling and test cases for both the client and server.

### Demonstration scenario:

- The client and server are running on separate containers in bigubu.ii.pw.edu.pl
- A user connects to the server using the client and authenticates with a valid username and password
- The user views the contents of a local and remote directory and navigates through them
- The user switches between active and passive modes and transfers a file between the local and remote directories
- Another user connects to the server using the client and authenticates with a different username and password
- Both users are able to concurrently transfer files between their local and remote directories
- The demonstration ends with all connections closed and all transferred files successfully stored in the appropriate locations.


### Tests:

We run a server on our local machine, using docker container with command `sh Docker.sh` being in /server.
```
CONTAINER ID   IMAGE        COMMAND            CREATED              STATUS              PORTS                                                                                                                                             NAMES
8c2bee8478c7   ftp_server   "python main.py"   About a minute ago   Up About a minute   0.0.0.0:21->21/tcp, :::21->21/tcp, 0.0.0.0:990->990/tcp, :::990->990/tcp, 0.0.0.0:65000-65534->65000-65534/tcp, :::65000-65534->65000-65534/tcp   ftp_server
```

To run our clients on local machine we type command `python3 main.py` being in /client.

- Use case 1:

Description: We run client side with command written before.
Success: program starts and we see first welcome message.
Exception: program does not start and error is showing.  
 
Result:
```
Welcome to FTP client
Type HELP for a list of commands
>
```

- Use case 2:

Description: client connects to the server on the local machine.
Success: clients connects successfully and have message with code 220.
Exception: clients can not connect to server, because of internet connection or server does not work.
Precondition: client and server have internet connection.

Result: 
```
> CONNECT
220 Welcome to FTP server
Connected to server
Passive mode activated by default
Binary mode activated by default
```

- Use case 3:

Description: client authenticates with the server using a valid username and password.
Success: user authenticates successfully and gets message with code 230.
Exception: user can not authenticate, login or password is incorrect, so it is shown message with code 530 about refusal authentication and code 221. 

Result with success: 
```
> USER ftp_user
USER ftp_user

331 Please specify the password

> PASS abcd    
PASS abcd

230 Login successful
```

Result with failure:
```
> USER sdfsdv
USER sdfsdv

331 Please specify the password

> PASS cfbcfb
PASS cfbcfb

530 Login incorrect
221 Goodbye
```

Use case 4:

Description: client sees list of files in current directory on local machine.
Success: list is showed successfully.
Exception: list is not showing.

Result: 
```
> ls
main.py
test
certs
```

Use case 5:

Description: client creates a directory on local machine.
Success: new directory is correctly created.
Exception: new directory is not created.

Result: 
```
> mkdir myfolder
> ls
main.py
test
myfolder
certs
```

Use case 6: 
Description: client changes directory and can see it on local machine.
Success: directory is correctly changed.
Exception: directory is not changed.

Result: 
```
> cd myfolder
> pwd
/client/myfolder
```

Use case 7: 
Description: client views the contents of remote directory in passive mode.
Success: list is showed successfully, firstly we have directory listening with code 150 and then see the content with code 226.
Exception: list is not showed.

Result: 
```
> LIST
227 Entering Passive Mode (0,0,0,0,254,148)
LIST

150 Here comes the directory listing.

drwxr-xr-x 2 ftp_user ftp_user 4096 Jan 20 21:40 .
drwxr-xr-x 1 root     root     4096 Jan 20 21:40 ..
-rw-r--r-- 1 ftp_user ftp_user  220 Mar 27  2022 .bash_logout
-rw-r--r-- 1 ftp_user ftp_user 3526 Mar 27  2022 .bashrc
-rw-r--r-- 1 ftp_user ftp_user  807 Mar 27  2022 .profile
226 Directory send OK.
```

Use case 8: 
Description: client creates a directory on remote machine in passive mode.
Success: new directory is correctly created with code 257.
Exception: new directory is not created.

Result: 
```
> MKD remote_folder
MKD remote_folder

257 Directory created.
```

Use case 9: 
Description: client changes remote directory and can see it.
Success: directory is correctly changed with code 250 and see current directory with code 257.
Exception: directory is not changed, direcotory name is incorrect.

Result: 
```
> CWD remote_folder
CWD remote_folder

250 CWD command successful

> PWD
PWD

257 "/ftp_user/remote_folder"
```

Exception:
```
> CWD dfvdf
CWD dfvdf

550 Error changing directory
```

Use case 10: 
Description: client transports a file from local machine to remote machine in passive mode.
Success: file is transported successfully with code 150.
Exception: file is not transported.

Result: 
```
> STOR readme_new.txt
227 Entering Passive Mode (0,0,0,0,254,143)

STOR readme_new.txt

150 Opening data connection.

File uploaded successfully

> LIST
227 Entering Passive Mode (0,0,0,0,254,7)

LIST

150 Here comes the directory listing.

drwxr-xr-x 2 root     root     4096 Jan 20 22:54 .
drwxr-xr-x 3 ftp_user ftp_user 4096 Jan 20 22:44 ..
-rw-r--r-- 1 ftp_user ftp_user   22 Jan 20 22:54 readme_new.txt
226 Directory send OK.
```


Use case 11: 
Description: client renames a file on remote machine in passive mode.
Success: file is successfully found with code 350 and correctly renamed with code 250.
Exception: file is not renamed.

Result: 
```
> REN readme_new.txt readme_renamed.txt
RNFR readme_new.txt

350 File exists, ready for destination name.

RNTO readme_renamed.txt

250 File renamed.
```

Use case 12: 
Description: client downloades a file from remote machine to local machine.
Success: file is downloaded correctly with code 150.
Exception: file is not downloaded.

Result: 
```
> RETR readme_renamed.txt
227 Entering Passive Mode (0,0,0,0,254,13)

RETR readme_renamed.txt

150 Opening data connection for file transfer.

File downloaded successfully

> ls
readme_new.txt
readme_renamed.txt
readme.txt
```

Use case 13: 
Description: client removes a file on remote machine in passive mode.
Success: file is correctly removed with code 250.
Exception: file is not removed.

Result: 
```
> DELE readme_renamed.txt
DELE readme_renamed.txt

250 File deleted.

> LIST
227 Entering Passive Mode (0,0,0,0,253,243)

LIST

150 Here comes the directory listing.

drwxr-xr-x 2 root     root     4096 Jan 20 23:04 .
drwxr-xr-x 3 ftp_user ftp_user 4096 Jan 20 22:44 ..
226 Directory send OK.
```

Use case 14: 
Description: client removes a directory on remote machine in passive mode.
Success: directory is correctly removed with code 250.
Exception: file is not removed.

Result: 
```
> RMD remote_folder
RMD remote_folder

250 Directory removed.

> LIST
227 Entering Passive Mode (0,0,0,0,254,184)

LIST

150 Here comes the directory listing.

drwxr-xr-x 2 ftp_user ftp_user 4096 Jan 20 23:06 .
drwxr-xr-x 1 root     root     4096 Jan 20 21:40 ..
-rw-r--r-- 1 ftp_user ftp_user  220 Mar 27  2022 .bash_logout
-rw-r--r-- 1 ftp_user ftp_user 3526 Mar 27  2022 .bashrc
-rw-r--r-- 1 ftp_user ftp_user  807 Mar 27  2022 .profile
226 Directory send OK.
```

Use case 15: 
Description: two clients authenticate to one server in paralel mode.
Success: both clients are authenticated successfully.
Exception: clients are not authenticated.

Result: 
```
> USER ftp_user
USER ftp_user

331 Please specify the password

> PASS abcd
PASS abcd

230 Login successful
---

> USER ftp_user2
USER ftp_user2

331 Please specify the password

> PASS abcd
PASS abcd

230 Login successful
```

Use case 16:

Description: sever works with both clients and have two folders for them.
Success: we can see two folders of both clients in remote directory and both client view list of files successfully.
Exception: server does not work with two clients in paralel.

Result: 
```
> LIST
227 Entering Passive Mode (0,0,0,0,254,196)

LIST

150 Here comes the directory listing.

drwxr-xr-x 1 root      root      4096 Jan 20 21:40 .
drwxr-xr-x 1 root      root      4096 Jan 20 21:40 ..
drwxr-xr-x 2 ftp_user  ftp_user  4096 Jan 20 23:06 ftp_user
drwxr-xr-x 2 ftp_user2 ftp_user2 4096 Jan 20 21:40 ftp_user2
226 Directory send OK.

---
> LIST
227 Entering Passive Mode (0,0,0,0,254,59)

LIST

150 Here comes the directory listing.

drwxr-xr-x 2 ftp_user2 ftp_user2 4096 Jan 20 21:40 .
drwxr-xr-x 1 root      root      4096 Jan 20 21:40 ..
-rw-r--r-- 1 ftp_user2 ftp_user2  220 Mar 27  2022 .bash_logout
-rw-r--r-- 1 ftp_user2 ftp_user2 3526 Mar 27  2022 .bashrc
-rw-r--r-- 1 ftp_user2 ftp_user2  807 Mar 27  2022 .profile
226 Directory send OK.

---
> LIST
227 Entering Passive Mode (0,0,0,0,254,108)

LIST

150 Here comes the directory listing.

drwxr-xr-x 2 ftp_user ftp_user 4096 Jan 20 23:06 .
drwxr-xr-x 1 root     root     4096 Jan 20 21:40 ..
-rw-r--r-- 1 ftp_user ftp_user  220 Mar 27  2022 .bash_logout
-rw-r--r-- 1 ftp_user ftp_user 3526 Mar 27  2022 .bashrc
-rw-r--r-- 1 ftp_user ftp_user  807 Mar 27  2022 .profile
226 Directory send OK.
```


