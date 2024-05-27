import psycopg2
import json
import db


import boto3
from botocore.exceptions import ClientError



def handler(event, context):

    connection = db.connect()

    print("initializing")
  
    try:

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

        cursor = connection.cursor()
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Tools (
                toolID UUID PRIMARY KEY,
                userID UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        connection.commit()
        print('Table "Tools" created successfully')

        cursor = connection.cursor()
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
        connection.commit()
        print('Table "APIKeys" created successfully')


        cursor = connection.cursor()
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS Policies (
                policyID UUID PRIMARY KEY,
                userID UUID NOT NULL,
                allow_tools BOOLEAN NOT NULL,
                allow_vfs BOOLEAN NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        connection.commit()
        print('Table "Policies" created successfully')

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
                status_time TIMESTAMP NOT NULL
            );
        """
        cursor.execute(create_table_sql)
        connection.commit()
        print('Table "Tasks" created successfully')


        # =========================== TEMP ==============================
        # import uuid
        # policy_1 = str(uuid.uuid4())
        # policy_2 = str(uuid.uuid4())

        # cursor = connection.cursor()

        # cursor.execute(f"""
        #     INSERT INTO Policies (policyID, userID, allow_tools, allow_vfs)
        #     VALUES ('{policy_1}', 'a9ae7c0d-8c5f-4bcf-8cb0-119a1fa8ca79', 'true', 'true')
        # """)

        # cursor.execute(f"""
        #     INSERT INTO Policies (policyID, userID, allow_tools, allow_vfs)
        #     VALUES ('{policy_2}', 'ed6bdfdb-28c9-41f3-8c73-0ad31c6aa2aa', 'true', 'true')
        # """)
        # print("policy initialization successful. changes not committed.")

        # connection.commit()
        # print("policy changes committed.")
        # =========================== TEMP ==============================


        # sql_query = "select * from information_schema.columns where table_schema = 'public'"
        # sql_query = "DROP TABLE Tasks"
        # cursor.execute(sql_query)
        # connection.commit()
        # print(cursor.fetchall())

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()
