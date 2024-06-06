import db
import json

# NOTE:
# Need to figure out how to fetch VFS that have been shared

def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:        
        user = event['requestContext']['authorizer']['userID']
        
        query = None
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:

            if 'name' in event['queryStringParameters']:
                vfs_name = event['queryStringParameters']['name']
                query = f"""
                    SELECT name, vfsID FROM VirtualFileSystems WHERE userID = '{user}' AND name = '{vfs_name}'
                """
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps("Error: Invalid query string")
                }
        else:
            query = f"""
                SELECT name, vfsID FROM VirtualFilesystems WHERE userID = '{user}'
            """

        cursor.execute(query)
        available_vfs = cursor.fetchall()
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(available_vfs)
        }
    
    except Exception as e:
        print(f'Error: {e}')
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Error listing filesystems')
        }
    finally:
        cursor.close()
        connection.close()
        
    
