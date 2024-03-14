import db

def list_vfs(user):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT name FROM VirtualFileSystems WHERE userID = '{user}'
    """
    cursor.execute(sql_query)
    available_vfs = cursor.fetchall()

    cursor.close()
    connection.close()

    return [vfs[0] for vfs in available_vfs]


def get_vfs_id(user, vfs_name):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT vfsID FROM VirtualFileSystems 
        WHERE userID = '{user}' 
        AND name = '{vfs_name}'
    """
    cursor.execute(sql_query)
    vfs_id = cursor.fetchall()

    cursor.close()
    connection.close()

    return vfs_id[0][0]

def get_vfs_name(user, vfs_id):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT name FROM VirtualFileSystems 
        WHERE userID = '{user}' 
        AND vfsID = '{vfs_id}'
    """
    cursor.execute(sql_query)
    vfs_name = cursor.fetchall()

    cursor.close()
    connection.close()

    return vfs_name[0][0]


def delete_by_id(user, vfs_id):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        DELETE FROM VirtualFileSystems 
        WHERE vfsID = '{vfs_id}' 
        AND userID = '{user}' 
    """
    cursor.execute(sql_query)
    connection.commit()
    cursor.close()
    connection.close()

def delete_by_name(user, vfs_name):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        DELETE FROM VirtualFileSystems 
        WHERE name = '{vfs_name}' 
        AND userID = '{user}' 
    """
    cursor.execute(sql_query)
    connection.commit()
    cursor.close()
    connection.close()