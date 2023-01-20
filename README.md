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