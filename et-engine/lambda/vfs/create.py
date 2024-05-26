
import json
import boto3
import db
import lambda_utils
import uuid

# def get_user(event):
#     cognito = boto3.client('cognito-idp')
#     response = cognito.get_user(
#         AccessToken=event['authorizationToken']
#     )

def handler(event, context):
    """
    creates a new filesystem under the specified user
    """

    # Get user
    try:
        user = event['requestContext']['authorizer']['userID']
        body = json.loads(event['body'])
        vfs_name = body['name']
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Parse Error: {e}')
        }


    # List all available vfs
    connection = db.connect()
    cursor = connection.cursor()
    try:

        # TURN TO SQL QUERY
        print('Fetching Available Tools..')

        sql_query = f"""
            SELECT name FROM VirtualFilesystems WHERE userID = '{user}'
        """
        cursor.execute(sql_query)
        available_vfs = [row[0] for row in cursor.fetchall()]
        print(f"Available VFS: {available_vfs}")


        if vfs_name in available_vfs:
            print(f"VFS {vfs_name} already exists")
            return {
                'statusCode': 500,
                    'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(f"Failed: '{vfs_name}' already exists")
            }
        
        else:

            vfs_id = str(uuid.uuid4())

            # >>>>> s3 bucket goes here
            cfn = boto3.client('cloudformation')

            parameters = [
                {
                    'ParameterKey': 'vfsID',
                    'ParameterValue': vfs_id
                }
            ]
            print(vfs_id, parameters)
            
            cfn.create_stack(
                StackName='vfs-' + vfs_id,
                TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/efs-basic.yaml',
                Parameters=parameters,
                Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
            )
            print('CREATING STACK')

            # =====
            # bucket_name = "vfs-" + vfs_id
            # s3 = boto3.client('s3')
            # s3.create_bucket(
            #     Bucket = bucket_name,
            #     CreateBucketConfiguration={
            #         'LocationConstraint': 'us-east-2'
            #     },
            # )
            # <<<<<

            cursor.execute(
                f"""
                INSERT INTO VirtualFileSystems (vfsID, userID, name)
                VALUES ('{vfs_id}', '{user}', '{vfs_name}')
                """
            )
            print("ROW INSERTED. NOT YET COMMITTED")
            connection.commit()
            print("ROW COMMITTED")


            return {
                'statusCode': 200,
                    'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(f"VFS '{vfs_name}' created")
            }
        
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Creation Error: {e}')
        }
    finally:
        cursor.close()
        connection.close()



