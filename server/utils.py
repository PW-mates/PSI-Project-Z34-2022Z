import os
import pwd
import spwd
import crypt
from models import User

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