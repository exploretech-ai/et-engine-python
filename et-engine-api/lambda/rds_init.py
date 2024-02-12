import psycopg2
import json
# from aws_cdk import core
# from aws_secretsmanager import Secret

# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError


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

    # Your code goes here.

def handler(event, context):

    # Load the Secrets Manager secret
    print("obtaining secret")
    db_secret = json.loads(get_secret())

    # # Connect to the database
    print("establishing connection")
    connection = psycopg2.connect(
        host=db_secret['host'],
        port=db_secret['port'],
        user=db_secret['username'],
        password=db_secret['password'],
        database="EngineMasterDB"
    )

    print("initializing")
  
    try:
        cursor = connection.cursor()
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Users (
                userID VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        connection.commit()

        print("Table 'users' created successfully!")

        cursor = connection.cursor()
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Algorithms (
                algoID UUID PRIMARY KEY,
                userID VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        connection.commit()

        

        print("Table 'algorithms' created successfully!")
        # sql_query = "select * from information_schema.columns where table_schema = 'public' and table_name   = 'users'"
        # sql_query = "DROP TABLE Algorithms"
        # cursor.execute(sql_query)
        # connection.commit()
        # print(cursor.fetchall())

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()
