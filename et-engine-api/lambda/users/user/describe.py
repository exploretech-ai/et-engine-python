import json
import uuid
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
import psycopg2

# from . import rds_create_user

def get_secret():

    secret_name = "RDSSecretA2B52E34-LB4TeGxLXYiz"
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


def connect():
    print("obtaining secret")
    db_secret = json.loads(get_secret())

    # # Connect to the database
    print("establishing connection")
    return psycopg2.connect(
        host=db_secret['host'],
        port=db_secret['port'],
        user=db_secret['username'],
        password=db_secret['password'],
        database="EngineMasterDB"
    )



def handler(event, context):
    '''
    Creates a new algorithm ID and pushes to the database
    '''
    try:
        userID = event['pathParameters']['userID']
        connection = connect()
        with connection.cursor() as cursor:

            sql_query = f"SELECT * FROM Users  WHERE userID = '{userID}'"
            cursor.execute(sql_query)
            data = cursor.fetchall()

        # Commit the changes
        connection.commit()
        return {
            'statusCode': 200,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps(data)
        }

    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error creating user {e}')
        }
        
