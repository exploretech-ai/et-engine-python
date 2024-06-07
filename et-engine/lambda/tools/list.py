import json
import db

# NOTE:
# Need to figure out how to fetch tools that have been shared

def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:
        user = event['requestContext']['authorizer']['userID']
        print(user)

        query = None
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:

            query = f"""SELECT name FROM Tools WHERE userID = '{user}'"""
            if 'name' in event['queryStringParameters']:
                tool_name = event['queryStringParameters']['name']

                query = f"""
                    SELECT name, toolID FROM Tools WHERE userID = '{user}' AND name = '{tool_name}'
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
                SELECT name, toolID FROM Tools WHERE userID = '{user}'
            """
            

        cursor.execute(query)
        print(f'Found {cursor.rowcount} owned tools')
        available_tools = cursor.fetchall()
        print('Owned tools:', available_tools)

        # >>>>> Listing shared VFS
        query = """
            SELECT 
                name, toolID 
            FROM
                Tools
            INNER JOIN Sharing
                ON Tools.toolID = Sharing.resourceID AND Sharing.resource_type = 'tools' AND Sharing.granteeID = %s
        """
        cursor.execute(query, (user,))
        print(f'Found {cursor.rowcount} shared tools')
        shared_tools = cursor.fetchall()
        print('Shared tools:', shared_tools)
        

        for tool in available_tools:
            tool = tool + ("owned",)
        for tool in shared_tools:
            tool = tool + ("shared",)

        available_tools.extend(shared_tools)

        # <<<<<
        return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(available_tools)
            }
        
    except Exception as e:
        print(f'Error: {e}')
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Error listing tools')
        }
    finally:
        cursor.close()
        connection.close()
    
