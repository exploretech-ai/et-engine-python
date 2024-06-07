
import json
import db

def handler(event, context):
    """
    creates a new API key under the specified user
    """

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Error: user does not exist')
        }


    try:
    
        sql_query = f"""
            SELECT name, description, date_created, date_expired FROM APIKeys WHERE userID = '{user}'
        """
        print(sql_query)
    
        connection = db.connect()
        print('connected')

        cursor = connection.cursor()
        cursor.execute(sql_query)
        print('query executed')
        queried_keys = cursor.fetchall()
        print(queried_keys)

        cursor.close()
        connection.close()
        print('closed')

        api_keys = []
        for item in queried_keys:
            api_keys.append({
                'name': item[0],
                'description': item[1],
                'dateCreated': item[2].strftime('%Y-%m-%d %H:%M:%S'),
                'dateExpired': item[3].strftime('%Y-%m-%d %H:%M:%S')
            })

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(api_keys)
        }
        
    except Exception as e:
        print('ERROR:', e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'An error occurred while listing the keys')
        }


