from flask import Flask, send_file, send_from_directory, request, Response
import logging
import os
import json


def initialize():
    # See here for connection pool architecture
    # https://stackoverflow.com/questions/29565283/how-to-use-connection-pooling-with-psycopg2-postgresql-with-flask
    
    import boto3
    from botocore.exceptions import ClientError
    import psycopg2

    database_secret_name = os.environ['DATABASE_SECRET_NAME']
    database_name = os.environ['DATABASE_NAME']
    fernet_key_secret_name = os.environ['FERNET_KEY_SECRET_NAME']
    region_name = os.environ['SECRET_REGION']

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response_database_secret = client.get_secret_value(
            SecretId=database_secret_name
        )
        response_fernet_key_secret = client.get_secret_value(
            SecretId=fernet_key_secret_name
        )
    except ClientError as e:
        raise e
    
    database_secret = json.loads(response_database_secret['SecretString'])
    fernet_key_secret = response_fernet_key_secret['SecretString']
    
    connection = psycopg2.connect(
        host=database_secret['host'],
        port=database_secret['port'],
        user=database_secret['username'],
        password=database_secret['password'],
        database=database_name
    )
    return fernet_key_secret, connection


FERNET_KEY, CONNECTION = initialize()
CONNECTION.close()


# from auth.key_authorizer import AuthMiddleware

app = Flask(__name__)
# app.wsgi_app = AuthMiddleware(app.wsgi_app)



logger = logging.getLogger()
logger.setLevel(logging.INFO)


EFS_MOUNT_POINT = '/mnt/'

@app.route('/')
def hello():
    return "hello, world!"

@app.route('/vfs/<vfsID>/files/<path:filepath>', methods=['GET'])
def download_file(vfsID, filepath):

    logger.info(f"VFS: {vfsID}, File: {filepath}")

    full_file_path = os.path.join(EFS_MOUNT_POINT, vfsID, filepath)

    if "/../" in full_file_path:
        logger.info(f"** ALERT: POTENTIALLY MALICIOUS PATH **")
        return "Invalid path", 403
    
    if not os.path.exists(full_file_path):
        return f"File '{filepath}' does not exist", 404

    def stream_file(file_to_stream):
        with open(file_to_stream, "rb") as file_object:
            while True:
                chunk = file_object.read(8192)
                if not chunk:
                    break
                yield chunk
            
    return Response(stream_file(full_file_path))
    
    # return send_from_directory(EFS_MOUNT_POINT + vfsID, filepath, as_attachment=True)


if __name__ == '__main__':

    environment = os.environ.get("ENV", "prod")

    if environment == 'dev':
        app.run(host="0.0.0.0", port=80)
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=80)
