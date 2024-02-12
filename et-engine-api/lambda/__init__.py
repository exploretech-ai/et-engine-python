import json
import psycopg2
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

def rds_get_user(userID):
    """GET /users/{userID}"""
    connection = connect()
    cursor = connection.cursor()

    # Define the SQL command to create a table
    sql_statement = f"""
        SELECT *
        FROM users
        WHERE userID = {userID}';
    """

    # # Execute the SQL command
    cursor.execute(sql_statement)

    # # Commit the changes to the database
    connection.commit()

    print("Table 'users' created successfully!")


def rds_get_algo(userID, algoID):
    """GET /users/{userID}/algorithms/{algoID}"""
    pass

def rds_create_user(userID, name):
    """POST /users"""
    connection = connect()
    with connection.cursor() as cursor:
        # Execute the SQL query to add an item to the table
        sql_query = f"INSERT INTO Users (userID, name) VALUES ('{userID}', '{name}')"
        cursor.execute(sql_query)

    # Commit the changes
    connection.commit()


def rds_create_algo(userID):
    """POST /users/{userID}/algorithms"""
    pass

