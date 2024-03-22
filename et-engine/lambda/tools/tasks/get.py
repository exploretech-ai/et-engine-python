import json
import boto3


def handler(event, context):

    # Checks whether the task definition is ready for execution
    # Ready for execution = repository is not empty
    # > ECR client
    # > 
    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        tool_id = event['pathParameters']['toolID']
        
        ecr = boto3.client('ecr')

        ready = False
        image_details = ecr.describe_images(repositoryName="tool-"+tool_id)['imageDetails']
        if image_details:
            ready = True


        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(ready)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f"error: {e}")
        }