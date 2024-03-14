import psycopg2
import json
import db
# from aws_cdk import core
# from aws_secretsmanager import Secret

# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError



def handler(event, context):

    connection = db.connect()

    print("initializing")
  
    try:
        # cursor = connection.cursor()
        # create_table_sql = """
        #     CREATE TABLE IF NOT EXISTS Users (
        #         userID VARCHAR(255) PRIMARY KEY,
        #         name VARCHAR(255) NOT NULL
        #     );
        # """
        # cursor.execute(create_table_sql)
        # connection.commit()
        # print("Table 'users' created successfully!")

        # cursor = connection.cursor()
        # create_table_sql = """
        #     CREATE TABLE IF NOT EXISTS Workflows (
        #         workflowID UUID PRIMARY KEY,
        #         userID VARCHAR(255) NOT NULL,
        #         name VARCHAR(255) NOT NULL,
        #         graph VARCHAR
        #     );
        # """
        # cursor.execute(create_table_sql)
        # connection.commit()
        # print("Table 'workflows' created successfully!")

        cursor = connection.cursor()
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS VirtualFileSystems (
                vfsID UUID PRIMARY KEY,
                userID UUID NOT NULL,
                name VARCHAR(255) NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        connection.commit()
        print('Table "VirtualFileSystems" created successfully')


        sql_query = "select * from information_schema.columns where table_schema = 'public'"
        # sql_query = "DROP TABLE VirtualFileSystems"
        cursor.execute(sql_query)
        # connection.commit()
        print(cursor.fetchall())

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()
