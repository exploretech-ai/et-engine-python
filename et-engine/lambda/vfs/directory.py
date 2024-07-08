import json
import boto3
import db


def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:
        user_id = event['requestContext']['authorizer']['userID']
        vfs_id = event['pathParameters']['vfsID']
        path = event["queryStringParameters"]['path']

        # If so, call the lambda with the request type: "list"
        lam = boto3.client('lambda')

        response = lam.invoke(
            FunctionName="vfs-"+vfs_id,
            Payload=json.dumps(
                {
                    "operation" : "list",
                    "path" : "/mnt/efs/" + path
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
            'body': json.dumps({
                'directories': body['directories'],
                'files': body['files']
            })
        }
        
    # except NameError as e:
    #     print(e)
    #     return {
    #         'statusCode': 401,
    #         'headers': {
    #             'Access-Control-Allow-Origin': '*'
    #         },
    #         'body': json.dumps(f'Could not access VFS')
    #     }
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

    
# if __name__ == "__main__":
#     files = [
#     ]

#     directory = []
#     for file in files:
#         directory.append(file.split('/'))


#     hierarchy = {}
#     for file in directory:
#         current_branch = hierarchy
#         for component in file[:-1]:
#             if component in current_branch:
#                 current_branch = current_branch[component]
#             else:
#                 current_branch[component] = {}
#                 current_branch = current_branch[component]
#         current_branch[file[-1]] = None

#     print(hierarchy)

        