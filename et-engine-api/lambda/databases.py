import boto3

def fetch_algo_ID():

    dynamodb = boto3.resource('dynamodb')
    table_name = 'UserResourceLog'
    table = dynamodb.Table(table_name)

    tbl_response = table.get_item(Key = {'UserID': '0'})
    item = tbl_response.get('Item')

    return item['algo_ID']

def get_stack_outputs(algo_ID):

    cf_client = boto3.client('cloudformation')
    stackname = f'engine-cfn-{algo_ID}'

    cf_response = cf_client.describe_stacks(StackName=stackname)
    return cf_response["Stacks"][0]["Outputs"]


def get_output_value(outputs, key):
    value = None
    for elem in outputs:
        if elem["OutputKey"] == key:
            value = elem["OutputValue"]

    if value is None:
        raise Exception("Key {key} not found")
    
    return value
    
