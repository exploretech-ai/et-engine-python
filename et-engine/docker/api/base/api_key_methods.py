from flask import Blueprint, Response, request
import json
import uuid
import datetime
from cryptography.fernet import Fernet
from base import CONNECTION_POOL, FERNET_KEY

keys = Blueprint('keys', __name__)


@keys.route('/keys', methods=['GET'])
def list_keys():
    """
    List all API keys for the authenticated user.

    This endpoint retrieves all API keys associated with the authenticated user.
    The user is identified by the 'user_id' in the request context.

    :reqheader Authorization: Bearer token for user authentication
    :status 200: Success. Returns a list of API keys.
    :status 500: Unknown error occurred during processing.

    **Example response**:

    .. sourcecode:: json

       [
         {
           "name": "API Key Name",
           "description": "Key Description",
           "dateCreated": "2024-07-16 10:30:00",
           "dateExpired": "2024-08-15 10:30:00"
         }
       ]

    :raises: May raise exceptions related to database operations.
    """

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT name, description, date_created, date_expired FROM APIKeys WHERE userID = %s
            """,
            (user_id,)
        )
        queried_keys = cursor.fetchall()

        api_keys = []
        for item in queried_keys:
            api_keys.append({
                'name': item[0],
                'description': item[1],
                'dateCreated': item[2].strftime('%Y-%m-%d %H:%M:%S'),
                'dateExpired': item[3].strftime('%Y-%m-%d %H:%M:%S')
            })

        return Response(json.dumps(api_keys), status=200)
    
    except:
        return Response("Unknown error", status=500)

    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@keys.route('/keys', methods=['POST'])
def create_key():
    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)

    except Exception as e:
        return Response("Error parsing request body", status=400)

    try:
        key_name = body['name']
        key_description = body['description']
    
    except KeyError as e:
        return Response("Request missing name or description", status=400)
    
    except Exception as e:
        return Response("Error parsing request body", status=400)

    key_id = str(uuid.uuid4())
        
    create_time = datetime.datetime.now()
    expired_time = create_time + datetime.timedelta(days=30)

    create_time = create_time.strftime('%Y-%m-%d %H:%M:%S')
    expired_time = expired_time.strftime('%Y-%m-%d %H:%M:%S')

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        if check_if_key_name_exists(cursor, user_id, key_name):
            return Response("API Key with same name already exists", status=409)
        else:
            insert_new_key(cursor, key_id, user_id, key_name, key_description, create_time, expired_time)
            connection.commit()
            return Response(status=200)
        
    except:
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@keys.route('/keys/<key_id>', methods=['DELETE'])
def delete_key(key_id):
    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            DELETE FROM APIKeys WHERE userID=%s AND keyID=%s
            """,
            (user_id, key_id)
        )
        connection.commit()
        
    except:
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


def insert_new_key(cursor, key_id, user_id, key_name, key_description, create_time, expired_time):
    f = Fernet(FERNET_KEY)
    key_token = f.encrypt(str.encode(key_id)).decode()
    
    cursor.execute(
        """
        INSERT INTO APIKeys (keyID, userID, name, description, date_created, date_expired)
        VALUES ('{key_id}', '{user}', '{key_name}', '{key_description}', '{create_time}', '{expired_time}')
        """,
        (
            key_id,
            user_id,
            key_name,
            key_description,
            create_time,
            expired_time
        )
    )

    return {
        'name': key_name,
        'key': key_token,
        'dateCreated': create_time,
        'dateExpired': expired_time
    }


def check_if_key_name_exists(cursor, user_id, desired_name):
    
    cursor.execute(
        """
        SELECT name FROM APIKeys WHERE userID = %s
        """,
        (user_id,)
    )

    queried_keys = cursor.fetchall()
    available_names = [name[0] for name in queried_keys]
    
    return desired_name in available_names
        