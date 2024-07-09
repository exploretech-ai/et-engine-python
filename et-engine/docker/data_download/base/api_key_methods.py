from flask import Blueprint, Response, request
import json
from . import CONNECTION_POOL

keys = Blueprint('keys', __name__)


@keys.route('/keys', methods=['GET'])
def list_keys():

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
    pass


@keys.route('/keys', methods=['DELETE'])
def delete_key():
    pass

