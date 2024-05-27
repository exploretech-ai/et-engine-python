import json
import lambda_utils
import db

def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:
        user = event['requestContext']['authorizer']['userID']
        
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:

            if 'name' in event['queryStringParameters']:
                vfs_name = event['queryStringParameters']['name']

                sql_query = f"""
                    SELECT vfsID FROM VirtualFilesystems WHERE userID = '{user}' AND name = '{vfs_name}'
                """
                cursor.execute(sql_query)
                vfs_id = cursor.fetchall()
                
                if len(vfs_id) == 0:
                    raise NameError('no tool id found')
                else:
                    vfs_id = vfs_id[0][0]
                    print(f"Delete Request for ID: {vfs_id}")
                
                

                sql_query = f"""
                    DELETE FROM VirtualFilesystems WHERE userID = '{user}' AND name = '{vfs_name}'
                """
                cursor.execute(sql_query)
                connection.commit()
                print("VFS Deleted from database")

                print("Emptying bucket")
                lambda_utils.empty_bucket("vfs-"+vfs_id)
                print("Deleting stack")
                lambda_utils.delete_stack("vfs-"+vfs_id)
                print("DELETE SUCCESSFUL")


                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(f"'{vfs_name}' deleted")
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps("Error: Invalid query string")
                }
        else:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps("Error: must include query string")
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Error: {e}')
        }
    finally:
        cursor.close()
        connection.close()
    
    
