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

def list_tools(user):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT name FROM Tools WHERE userID = '{user}'
    """
    cursor.execute(sql_query)
    available_tools = cursor.fetchall()

    cursor.close()
    connection.close()

    return [t[0] for t in available_tools]

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

def get_tool_id(user, tool_name):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT toolID FROM Tools 
        WHERE userID = '{user}' 
        AND name = '{tool_name}'
    """
    cursor.execute(sql_query)
    tool_id = cursor.fetchall()

    cursor.close()
    connection.close()

    return tool_id[0][0]

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

def get_tool_name(user, tool_id):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT name FROM Tools 
        WHERE userID = '{user}' 
        AND toolID = '{tool_id}'
    """
    cursor.execute(sql_query)
    tool_name = cursor.fetchall()

    cursor.close()
    connection.close()

    return tool_name[0][0]


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

def delete_tool_by_id(user, tool_id):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        DELETE FROM Tools 
        WHERE toolID = '{tool_id}' 
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