import json
import boto3

class NotOwnerError(Exception):
    pass

def handler(event, context):

    # connection = db.connect()
    # cursor = connection.cursor()
    try:
        user_id = event['requestContext']['authorizer']['userID']
        vfs_id = event['pathParameters']['vfsID']
        file_path = event['pathParameters']['filepath']

        print(f"Delete Requested for: {file_path}")
        print(f"on VFS {vfs_id}")
        print(f"by User {user_id}")

        is_owned = json.loads(event['requestContext']['authorizer']['isOwned'])
        if not is_owned:
            raise NotOwnerError


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
    
    except NotOwnerError as e:
        print('ERROR: MUST BE OWNER OF RESOURCE TO DELETE', e)
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps("must be owner to delete")
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
    

    

        