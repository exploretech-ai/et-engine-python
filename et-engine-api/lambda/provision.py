import boto3
import json
from datetime import datetime
import uuid

def ConfigStorage(storage_config, algo_ID):
    if storage_config == 'new':

        # Bucket needs to be specified via: FileSystem-UserID-ResourceID
        bucket_name = f"engine-s3-0-{algo_ID}"

    else:
        raise Exception(f"storage configuration '{storage_config}' not recognized")
        
    # Create Bucket
    bucket_stack = {
        "Type": "AWS::S3::Bucket",
        "Properties": {
            "BucketName": bucket_name
        }
    }
    
    return bucket_stack

def ConfigCompute(compute_config, algo_ID):
    if compute_config == 'SingleNode':
        instance_name = f"engine-cpu-0-{algo_ID}"
    
    else:
        raise Exception(f"instace type '{compute_config}' not recognized")
    
    # PROVISIONING GOES HERE
    # 1. New ECR Repository
    compute_stack = {}
    compute_stack['ContainerRepo'] = {
        "Type": "AWS::ECR::Repository",
        "Properties": {
            "RepositoryName": f"engine-ecr-0-{algo_ID}"
        }
    }


    # 2. ECS Fargate Task Definition
    task_stack = {
        "Type": "AWS::ECS::TaskDefinition",
        "Properties": {
            ""
        }
    }
    # 3. Container Image
    # 4. 

    return compute_stack

def ProvisionResources(config):
    algo_ID = uuid.uuid4().hex
    # Check if config gives you the keys: 'storage' and 'compute'

    storage_stack = ConfigStorage(config['storage'], algo_ID)
    compute_stack = ConfigCompute(config['compute'], algo_ID)

    template = {
        'Resources': compute_stack
    }
    template['Resources']['FileSystem'] = storage_stack


    cf = boto3.client('cloudformation')
    cf.create_stack(
        StackName = f"engine-cfn-{algo_ID}", 
        TemplateBody = json.dumps(template),
        OnFailure = 'DELETE'
    )

    return algo_ID



def handler(event, context):

    tbl_name = "UserResourceLog"
    current_datetime = datetime.now().isoformat()

    # Parse JSON
    try:
        request_body = json.loads(event['body'])
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"Incorrect POST format: got {event}")
        }
        return response

    # Attempt to Provision Resources
    try:
        algo_ID = ProvisionResources(request_body)
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f'Error provisioning resources: {e}')
        }
        return response

    # Write to table
    try:
        dynamodb = boto3.client('dynamodb')
        item_data = {
            "UserID": {'S': '0'},
            "time": {'S': current_datetime},
            "algo_ID": {'S': algo_ID}
        }
        dynamodb.put_item(TableName=tbl_name, Item=item_data)

        response = {
            'statusCode': 200,
            'body': json.dumps(f'Item added to DynamoDB table successfully: {item_data}')
        }       
    except Exception as e:
        print(f"Error: {e}")
        response = {
            'statusCode': 500,
            'body': json.dumps(f'Error adding item to DynamoDB table: {e}')
        }
        
    return response



    