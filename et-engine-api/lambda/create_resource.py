import boto3
import json
from datetime import datetime

def handler(event, context):
    tbl_name = "UserResourceLog"
    current_datetime = datetime.now().isoformat()

    try:
        request_body = json.loads(event['body'])
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps("Incorrect POST format: request must include a body, e.g. '{\"arg1\": \"val1\"}'")
        }
        return response

    
    try:
        client = boto3.client('dynamodb')
        
        item_data = {
            "UserID": {'S': '0'},
            "time": {'S': current_datetime}
        }

        client.put_item(TableName=tbl_name, Item=item_data)

        response = {
            'statusCode': 200,
            'body': json.dumps(f'Item added to DynamoDB table successfully: {request_body}')
        }

    except Exception as e:
        print(f"Error: {e}")
        response = {
            'statusCode': 500,
            'body': json.dumps(f'Error adding item to DynamoDB table: {e}')
        }
        
    return response