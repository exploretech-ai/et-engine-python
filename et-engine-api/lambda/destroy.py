import boto3
import json
from databases import fetch_algo_ID, get_stack_outputs, get_output_value


def empty_s3_bucket(bucket_name):
    # Create an S3 client
    s3 = boto3.client('s3')

    # List all objects in the bucket
    response = s3.list_objects_v2(Bucket=bucket_name)

    # Check if there are any objects in the bucket
    if 'Contents' in response:
        objects = response['Contents']

        # Delete each object in the bucket
        for obj in objects:
            s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
            print(f"Deleted object: {obj['Key']}")

        print(f"All objects in the bucket '{bucket_name}' have been deleted.")
    else:
        print(f"The bucket '{bucket_name}' is already empty.")


def handler(event, context):

    try:
            
        dynamodb = boto3.resource('dynamodb')
        table_name = 'UserResourceLog'
        table = dynamodb.Table(table_name)

        tbl_response = table.get_item(Key = {'UserID': '0'})
        item = tbl_response.get('Item')

        algo_ID = fetch_algo_ID()

        cf_client = boto3.client('cloudformation')
        stackname = f'engine-cfn-{algo_ID}'

        


        # DELETE BUCKETS HERE
        cf_outputs = get_stack_outputs(algo_ID)
        for bucket in ["CodeBuildBucketName", "FileSystemName"]:
            bucket_name = get_output_value(cf_outputs, bucket)
            empty_s3_bucket(bucket_name)
        


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