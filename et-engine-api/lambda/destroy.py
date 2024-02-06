import boto3
import json


def handler(event, context):

    try:
            
        dynamodb = boto3.resource('dynamodb')
        table_name = 'UserResourceLog'
        table = dynamodb.Table(table_name)

        tbl_response = table.get_item(Key = {'UserID': '0'})
        item = tbl_response.get('Item')

        cf_client = boto3.client('cloudformation')
        stackname = f'engine-cfn-{item["algo_ID"]}'

        cf_client.delete_stack(StackName=stackname)

        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': '{"message": "Delete Initiated"}',
        }
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"Error deleting: {e}")
        }

    return response