import json
import boto3


def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']

        # vfsID as a path parameter
        vfs_id = event['pathParameters']['vfsID'] 
        print(f"Requested VFS id: {vfs_id}")

        # check if 'key' exists in the body
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:
            key = event['queryStringParameters']['key']
        else:
            raise Exception
        
        lam = boto3.client('lambda')

        payload = json.dumps(
            {
                "operation" : "download",
                "key": key,
                "prefix": "/mnt/efs/",
                "vfs": "vfs-"+vfs_id
            }
        )
        print(f"Payload: {payload}")

        response = lam.invoke(
            FunctionName="vfs-"+vfs_id,
            Payload=payload
        )
        print(f"Lambda Response: {response}")

        payload = response['Payload']
        msg = payload.read()
        msg = msg.decode("utf-8")
        body = json.loads(msg)

        print(f"Payload Body: {body}")

        if body['statusCode'] != 200:
            raise Exception(f'bad payload, status code {body["statusCode"]}')
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps(body['presigned_url'])
        }   
     
    
    except Exception as e:
        print('ERROR:', e)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f"Error fetching file for download"),
        } 

    
    