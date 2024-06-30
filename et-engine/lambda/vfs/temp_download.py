import json
import boto3


def handler(event, context):

    try:
       
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:
            key = event['queryStringParameters']['key']
        else:
            raise Exception
        
        # Create presigned post
        s3 = boto3.client('s3', region_name="us-east-2")

        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': "temp-data-transfer-bucket-test", 
                'Key': key
            },
            ExpiresIn=60
        )


        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps(presigned_url)
        }   
    

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 501,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps("Error generating presigned url"),
        } 

    
    