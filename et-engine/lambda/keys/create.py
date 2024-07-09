
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
        
        create_time = datetime.datetime.now()
        expired_time = create_time + datetime.timedelta(days=30)

        create_time = create_time.strftime('%Y-%m-%d %H:%M:%S')
        expired_time = expired_time.strftime('%Y-%m-%d %H:%M:%S')

        connection = db.connect()
        
        if check_if_key_name_exists(connection, user, key_name):
            status_code = 200
            response = None
        else:
            response = insert_new_key(connection, key_id, user, key_name, key_description, create_time, expired_time)
            status_code = 201
        connection.close()

        return {
            'statusCode': status_code,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Creation Error: {e}')
        }


def insert_new_key(cursor, key_id, user, key_name, key_description, create_time, expired_time):
    f = Fernet(fernet_key)
    key_token = f.encrypt(str.encode(key_id)).decode()
    
    sql_query = f"""
        INSERT INTO APIKeys (keyID, userID, name, description, date_created, date_expired)
        VALUES ('{key_id}', '{user}', '{key_name}', '{key_description}', '{create_time}', '{expired_time}')
    """
    print(sql_query)

    # cursor = connection.cursor()
    
    cursor.execute(sql_query)
    # connection.commit()

    # cursor.close()

    return {
        'name': key_name,
        'key': key_token,
        'dateCreated': create_time,
        'dateExpired': expired_time
    }


def check_if_key_name_exists(connection, user, desired_name):
    
    sql_query = f"""
        SELECT name FROM APIKeys WHERE userID = '{user}'
    """

    cursor = connection.cursor()
    cursor.execute(sql_query)

    queried_keys = cursor.fetchall()
    available_names = [name[0] for name in queried_keys]

    cursor.close()
    
    return desired_name in available_names
        