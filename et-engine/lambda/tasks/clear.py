import json
import db

def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:
        user = event['requestContext']['authorizer']['userID']
        print('User requested clearing of all tasks: ', user)

        query = f"""
            DELETE FROM Tasks WHERE userID = '{user}'
        """
        print(query)

        cursor.execute(query)
        print('deleted tasks, waiting to commit...')
        connection.commit()

        print('Tasks successfully cleared')
        return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps("success")
            }
        
    except Exception as e:
        print('error: ', e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'error clearing tasks')
        }
    finally:
        cursor.close()
        connection.close()
    
