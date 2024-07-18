import os
import json
import boto3
from botocore.exceptions import ClientError


def initialize():
    # See here for connection pool architecture
    # https://stackoverflow.com/questions/29565283/how-to-use-connection-pooling-with-psycopg2-postgresql-with-flask

    database_secret_name = os.environ['DATABASE_SECRET_NAME']
    database_name = os.environ['DATABASE_NAME']
    region_name = os.environ['SECRET_REGION']

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response_database_secret = client.get_secret_value(SecretId=database_secret_name)

    except ClientError as e:
        raise e
    
    database_secret = json.loads(response_database_secret['SecretString'])
    
    connection_params = {
        "host":     database_secret['host'],
        "port":     database_secret['port'],
        "user":     database_secret['username'],
        "password": database_secret['password'],
        "database": database_name
    }

    return connection_params, os.environ['JOB_SUBMISSION_QUEUE_URL']


