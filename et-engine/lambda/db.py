import json
import psycopg2
import boto3
import os
from botocore.exceptions import ClientError


def get_secret():

    secret_name = os.environ['SECRET_NAME']
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    return get_secret_value_response['SecretString']


def connect():
    # print("obtaining secret")
    db_secret = json.loads(get_secret())

    # # Connect to the database
    # print("establishing connection")
    return psycopg2.connect(
        host=db_secret['host'],
        port=db_secret['port'],
        user=db_secret['username'],
        password=db_secret['password'],
        database=os.environ['DATABASE_SHORT_NAME']
    )
