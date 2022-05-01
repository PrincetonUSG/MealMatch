from sys import stdout
from database import new_connection, close_connection


def get_from_netid(netid, *args):
    query = """SELECT {} FROM users WHERE netid = %s""".format(", ".join(args))
    cur, conn = new_connection()
    cur.execute(query, [netid])
    row = cur.fetchone()
    close_connection(cur, conn)
    return row
    

""""Check if the logged-in user has created a profile"""
def exists(netid):
    return get_from_netid(netid, 'netid') != None


def get_profile(netid):
    keys = ["netid","name","year","major","phonenum","bio"]
    vals = get_from_netid(netid, *keys)
    
    if not vals:
        vals = [""] * len(keys)
    return dict(zip(keys, vals))


# Create profile for user and update MongoDB
def create_profile(netid, name, year, major, phonenum, bio):
    sql = "INSERT INTO users (NETID,NAME,YEAR,MAJOR,PHONENUM,BIO) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (netid, name, year, major, phonenum, bio)

    cur, conn = new_connection()
    cur.execute(sql, val)
    close_connection(cur, conn)

    print("Profile created for:", netid, file=stdout)
    return netid


def edit_profile(netid, name, year, major, phonenum, bio):
    sql = "UPDATE users SET NAME=%s,YEAR=%s,MAJOR=%s,PHONENUM=%s,BIO=%s WHERE NETID=%s"
    val = (name, year, major, phonenum, bio, netid)
    
    cur, conn = new_connection()
    cur.execute(sql, val)
    close_connection(cur, conn)

    print("Profile updated for:", netid, file=stdout)
    return netid
