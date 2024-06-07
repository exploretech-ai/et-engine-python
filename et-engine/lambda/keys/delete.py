
import json
import db


def handler(event, context):
    """
    deletes the API key from the database
    """

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        key_name = event['queryStringParameters']['name']

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Parse Error: {e}')
        }


    try:

        sql_query = f"""
            DELETE FROM APIKeys WHERE userID='{user}' AND name='{key_name}'
        """
        print(sql_query)

        connection = db.connect()
        cursor = connection.cursor()
        
        cursor.execute(sql_query)
        connection.commit()
    
        cursor.close()
        connection.close()

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        print('ERROR:', e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'An error occurred while deleting the key')
        }

