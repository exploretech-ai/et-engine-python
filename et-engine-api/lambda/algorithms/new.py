import json
import uuid
import boto3
from datetime import datetime


def get_db_name():

    cf_client = boto3.client('cloudformation')
    cf_response = cf_client.describe_stacks(StackName="ETEngine")
    cf_outputs = cf_response["Stacks"][0]["Outputs"]
    
    return get_output_value(cf_outputs, "AlgorithmDB")


def get_output_value(outputs, key):
    value = None
    for elem in outputs:
        if elem["OutputKey"] == key:
            value = elem["OutputValue"]

    if value is None:
        raise Exception("Key {key} not found")
    
    return value

def handler(event, context):
    '''
    Creates a new algorithm ID and pushes to the database
    '''

    
    try:
        algoID = uuid.uuid4().hex
        current_datetime = datetime.now().isoformat()

        dynamodb = boto3.client('dynamodb')
        item_data = {
            "userID": {'S': '0'},
            "created": {'S': current_datetime},
            "algoID": {'S': algoID}
        }
        table_name = get_db_name()
        dynamodb.put_item(TableName=table_name, Item=item_data)

        return {
            'statusCode': 200,
            'body': json.dumps(algoID)
        }   
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error creating algorithm: {e}')
        }
        
