class User:
    def __init__(self, username, password, uid, gid, gecos, home_dir, shell):
        self.username = username
        self.password = password
        self.uid = uid
        self.gid = gid
        self.gecos = gecos
        self.home_dir = home_dir
        self.shell = shell