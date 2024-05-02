import json
import psycopg2
import boto3
from botocore.exceptions import ClientError


def get_secret():

    secret_name = "RDSSecretA2B52E34-oFnaTiUxNkh4"
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
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
    return get_secret_value_response['SecretString']

    # Your code goes here.

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
        database="EngineMasterDB"
    )
