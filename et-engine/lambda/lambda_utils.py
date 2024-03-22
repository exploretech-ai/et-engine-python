import db
import boto3


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


def describe_tool(user, tool_id):
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT * FROM Tools 
        WHERE userID = '{user}' 
        AND toolID = '{tool_id}'
    """
    cursor.execute(sql_query)
    params = cursor.fetchall()

    cursor.close()
    connection.close()

    return params


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



def get_tool_stack(tool_id):

    cf_client = boto3.client('cloudformation')
    cf_response = cf_client.describe_stacks(StackName=f"tool-{tool_id}")
    cf_outputs = cf_response["Stacks"][0]["Outputs"]
    
    return cf_outputs

def get_component_from_outputs(outputs, key):
    value = None
    for elem in outputs:
        if elem["OutputKey"] == key:
            value = elem["OutputValue"]

    if value is None:
        raise Exception("Key {key} not found")
    
    return value

def get_tool_components(tool_id, keys):
    outputs = get_tool_stack(tool_id)

    components = {}
    for key in keys:
        components[key] = get_component_from_outputs(outputs, key)
        
    return components
    

def to_hierarchy(directory_contents):
    files = []
    for obj in directory_contents['Contents']:
        files.append(obj['Key'])

    directory = []
    for file in files:
        directory.append(file.split('/'))

    hierarchy = {}
    for file in directory:
        current_branch = hierarchy
        for component in file[:-1]:
            if component not in current_branch:
                current_branch[component] = {}
            current_branch = current_branch[component]
        current_branch[file[-1]] = None

    return hierarchy