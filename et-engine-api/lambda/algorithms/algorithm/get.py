import json
import boto3

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
    Gets the database entry for the algoID (specified in path)
    '''
    try:
        algoID = event['pathParameters']['id']
        table_name = get_db_name()

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        table_response = table.get_item(Key = {'algoID': algoID})
        item = table_response.get('Item')

        return {
            'statusCode': 200,
            'body': json.dumps(item)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"{e}")
        }

    