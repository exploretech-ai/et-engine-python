import json
import boto3
import lambda_utils


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
        
        # >>>>>
        # Create presigned url
        # s3 = boto3.client('s3')
        # bucket_name = "vfs-" + vfs_id
        # presigned_url = s3.generate_presigned_url(
        #     'get_object',
        #     Params={'Bucket': bucket_name, 'Key': key},
        #     ExpiresIn=60
        # )
        # return {
        #     'statusCode': 200,
        #     'headers': {
        #         'Access-Control-Allow-Origin': '*'
        #     },
        #     'body' : json.dumps(presigned_url)
        # }   
        # =====
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
        # <<<<<
        
    
    

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f"Error: {e}"),
        } 

    
    