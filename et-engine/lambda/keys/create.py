
import json
import boto3
import db
import lambda_utils
import uuid
import time    
import datetime
from cryptography.fernet import Fernet


fernet_key = b'IGE3pGK7ih1vDm4na0EmW-rYCqfnZKMaNR7ea1ose2s='
def handler(event, context):
    """
    creates a new API key under the specified user
    """

    # Get user
    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        body = json.loads(event['body'])
        key_name = body['name']
        key_description = body['description']

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Parse Error: {e}')
        }


    try:
    
        key_id = str(uuid.uuid4())
        

        f = Fernet(fernet_key)
        key_token = f.encrypt(str.encode(key_id)).decode()
        
        create_time = datetime.datetime.now()
        expired_time = create_time + datetime.timedelta(days=30)

        create_time = create_time.strftime('%Y-%m-%d %H:%M:%S')
        expired_time = expired_time.strftime('%Y-%m-%d %H:%M:%S')

        # connection = db.connect()
        # cursor = connection.cursor()
        sql_query = f"""
            INSERT INTO APIKeys (keyID, userID, name, description, date_created, date_expired)
            VALUES ('{key_id}', '{user}', '{key_name}', '{key_description}', '{create_time}', '{expired_time}')
        """
        print(sql_query)
        # cursor.execute(sql_query)
        # connection.commit()
        # cursor.close()
        # connection.close()


        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'name': key_name,
                'key': key_token,
                'dateCreated': create_time
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Creation Error: {e}')
        }



    # Check if "name" is in vfs & return error if so

    # If "name" is not in vfs:
    #     1. Generate vfsID
    #     2. Push [vfsID, name, userID] to table
    #     3. Create new s3 bucket
    #     4. Return vfsID

    return {
        'statusCode': 200,
        'body': json.dumps('hello, world')
    }