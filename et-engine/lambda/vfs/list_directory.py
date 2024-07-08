import json
import boto3


def handler(event, context):

    try:
        vfs_id = event['pathParameters']['vfsID']
        path = event["pathParameters"]['filepath']

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
        
    except Exception as e:
        print(f'500 Error: {e}')
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Uncaught Error')
        }


    
