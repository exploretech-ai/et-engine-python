import boto3
import json


def get_stack_output(algoID):

    cf_client = boto3.client('cloudformation')
    cf_response = cf_client.describe_stacks(StackName=f"engine-algo-{algoID}")
    cf_outputs = cf_response["Stacks"][0]["Outputs"]
    
    return cf_outputs


def get_output_value(outputs, key):
    value = None
    for elem in outputs:
        if elem["OutputKey"] == key:
            value = elem["OutputValue"]

    if value is None:
        raise Exception("Key {key} not found")
    
    return value



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


def empty_ecr_repo(repo_name):
    # Create an ECR client
    ecr_client = boto3.client('ecr')

    # Get a list of image details for the specified repository
    images = ecr_client.describe_images(repositoryName=repo_name)['imageDetails']

    if not images:
        print(f"No images found in the repository: {repo_name}")
        return
    
    for image in images:
        image_digest = image['imageDigest']
    
        ecr_client.batch_delete_image(
            repositoryName=repo_name,
            imageIds=[
                {'imageDigest': image_digest}
            ]
        )
        print(f"Deleted image with digest: {image_digest}")



def handler(event, context):

    try:
            
        algoID = event['pathParameters']['algoID']
        cf_client = boto3.client('cloudformation')
        cf_outputs = get_stack_output(algoID)

    except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error fetching stack: {e}")
            }
        
        

    try:

        # DELETE BUCKETS HERE
        
        for bucket in ["CodeBuildBucketName", "FileSystemName"]:
            bucket_name = get_output_value(cf_outputs, bucket)
            empty_s3_bucket(bucket_name)

    except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error emptying filesystems: {e}")
            }
    
    try:

        repo_name = get_output_value(cf_outputs, "ContainerRepoName")
        empty_ecr_repo(repo_name)
        
    except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps(f"Error emptying docker images: {e}")
            }
    
    try:

        cf_client.delete_stack(StackName=f"engine-algo-{algoID}")

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