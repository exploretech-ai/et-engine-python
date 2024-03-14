
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
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        body = json.loads(event['body'])
        vfs_name = body['name']
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Parse Error: {e}')
        }


    # List all available vfs
    try:
        available_vfs = lambda_utils.list_vfs(user)

        # check if name is in available_vfs
        if vfs_name in available_vfs:
            return {
                'statusCode': 500,
                'body': json.dumps(f"Failed: '{vfs_name}' already exists")
            }
        
        else:

            vfs_id = str(uuid.uuid4())

            connection = db.connect()
            cursor = connection.cursor()
            sql_query = f"""
                INSERT INTO VirtualFileSystems (vfsID, userID, name)
                VALUES ('{vfs_id}', '{user}', '{vfs_name}')
            """
            cursor.execute(sql_query)
            connection.commit()
            cursor.close()
            connection.close()

            # >>>>> s3 bucket goes here
            bucket_name = "vfs-" + vfs_id
            s3 = boto3.client('s3')
            s3.create_bucket(
                Bucket = bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': 'us-east-2'
                },
            )
            # <<<<<

            return {
                'statusCode': 200,
                'body': json.dumps(f"VFS '{vfs_name}' created")
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Creation Error: {e}')
        }



    # Check if "name" is in vfs & return error if so

    # If "name" is not in vfs:
    #     1. Generate vfsID
    #     2. Push [vfsID, name, userID] to table
    #     3. Create new s3 bucket
    #     4. Return vfsID

    return {
        'statusCode': 200,
        'body': json.dumps('hello, world')
    }