import boto3
from databases import fetch_algo_ID, get_stack_outputs, get_output_value
import json


def handler(event, context):
    try:
        algo_ID = fetch_algo_ID()
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error fetching algo ID "}),
        }

    try:
        
        file_content = json.loads(event['body'])
        # file_name = event['queryStringParameters']['filename']  # or any other way to get the file name
        
        ### ----- FETCH THIS SHIT HERE ----
        cf_outputs = get_stack_outputs(algo_ID)
        bucket_name = get_output_value(cf_outputs, "CodeBuildBucketName")

        s3 = boto3.client('s3')
        s3.put_object(Body=file_content["dockerfile"], Bucket=bucket_name, Key='.engine/dockerfile')
        s3.put_object(Body=file_content["app"], Bucket=bucket_name, Key='.engine/app.py')
        
        # COPY BUILDSPEC HERE

        # TRIGGER CODEBUILD HERE

        return {
            'statusCode': 200,
            'body': json.dumps({"message": f"Configuration complete"})
        }


    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Configuration error: {e}"}),
        }
    
    # Push dockerfile and app here
        
    # return response
    