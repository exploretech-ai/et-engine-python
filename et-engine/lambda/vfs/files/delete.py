import json
import boto3
import db



def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:
        user_id = event['requestContext']['authorizer']['userID']
        vfs_id = event['pathParameters']['vfsID']
        file_path = event['pathParameters']['filepath']

        print(f"Delete Requested for: {file_path}")
        print(f"on VFS {vfs_id}")
        print(f"by User {user_id}")

        # file = ""
        # if 'body' in event:
        #     body = json.loads(event['body'])
        #     file=body['file']
        # else:
        #     raise Exception


        # Check if vfs exists
        cursor.execute(
        f"""
        SELECT vfsID FROM VirtualFilesystems WHERE userID='{user_id}'
        """
        )

        available_vfs = [row[0] for row in cursor.fetchall()]
        if vfs_id not in available_vfs:
            print(available_vfs, vfs_id)
            raise NameError(f'VFS {vfs_id} not available')

        # If so, call the lambda with the request type: "list"
        lam = boto3.client('lambda')

        response = lam.invoke(
            FunctionName="vfs-"+vfs_id,
            Payload=json.dumps(
                {
                    "operation" : "delete",
                    "file" : "/mnt/efs/" + file_path
                }
            )
        )
        payload = response['Payload']
        msg = payload.read()
        msg = msg.decode("utf-8")
        body = json.loads(msg)

        if body['statusCode'] != 200:
            raise Exception('bad payload, status code not 200')


        print(body)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('success')
        }
        
    except NameError as e:
        print(e)
        return {
            'statusCode': 401,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Could not access VFS')
        }
    except Exception as e:
        print(f'500 Error: {e}')
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Uncaught Error')
        }
    finally:
        cursor.close()
        connection.close()

    

        