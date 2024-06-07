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
        print(f'Found {cursor.rowcount} owned filesystems')
        available_vfs = cursor.fetchall()
        print('Owned filesystems:', available_vfs)

        # >>>>> Listing shared VFS
        query = """
            SELECT 
                name, vfsID 
            FROM
                VirtualFileSystems
            INNER JOIN Sharing
                ON VirtualFileSystems.vfsID = Sharing.resourceID AND Sharing.resource_type = 'vfs' AND Sharing.granteeID = %s
        """
        cursor.execute(query, (user,))
        print(f'Found {cursor.rowcount} shared filesystems')
        shared_vfs = cursor.fetchall()
        print('Shared filesystems:', shared_vfs)
        
        for vfs in available_vfs:
            vfs = vfs + ("owned",)
        for vfs in shared_vfs:
            vfs = vfs + ("shared",)
            
        available_vfs.extend(shared_vfs)

        # <<<<<

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
        
    
