import psycopg2
import json
import db
import boto3
from botocore.exceptions import ClientError



def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()

    print("initializing")
  
    try:

        
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS VirtualFileSystems (
                vfsID UUID PRIMARY KEY,
                userID UUID NOT NULL,
                name VARCHAR(255) NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        print('Table "VirtualFileSystems" created successfully')

        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Tools (
                toolID UUID PRIMARY KEY,
                userID UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        print('Table "Tools" created successfully')

        create_table_sql = """
            CREATE TABLE IF NOT EXISTS APIKeys (
                keyID UUID PRIMARY KEY,
                userID UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                date_created TIMESTAMP NOT NULL,
                date_expired TIMESTAMP NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        print('Table "APIKeys" created successfully')
        

        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Tasks (
                taskID UUID PRIMARY KEY,
                taskArn TEXT NOT NULL,
                userID UUID NOT NULL,
                toolID UUID NOT NULL,
                logID UUID NOT NULL,
                start_time TIMESTAMP NOT NULL,
                hardware JSON NOT NULL,
                args JSON NOT NULL,
                status VARCHAR(255) NOT NULL,
                status_time TIMESTAMP NOT NULL,
                exit_reason TEXT,
                exit_code INTEGER
            );
        """
        cursor.execute(create_table_sql)
        print('Table "Tasks" created successfully')


        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Sharing (
                accessID UUID PRIMARY KEY,
                ownerID UUID NOT NULL,
                granteeID UUID NOT NULL,
                resource_type VARCHAR(255) NOT NULL,
                resourceID UUID NOT NULL,
                date_granted TIMESTAMP NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        print('Table "Sharing" created successfully')


        connection.commit()




        # =========== SCRATCH ===========
        # sql_query = "select * from information_schema.columns where table_schema = 'public'"
        # sql_query = "DROP TABLE Policies"
        # cursor.execute(sql_query)
        # connection.commit()
        # print(cursor.fetchall())

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()
