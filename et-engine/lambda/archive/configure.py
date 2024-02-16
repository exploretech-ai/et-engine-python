import boto3
from databases import fetch_algo_ID, get_stack_outputs, get_output_value
import json


def copy_bucket(dest_bucket):

    cf_client = boto3.client('cloudformation')
    main_stack = cf_client.describe_stacks(StackName='EtEngineApiStack')
    main_stack_outputs = main_stack["Stacks"][0]["Outputs"]

    copy_source = {
        'Bucket': get_output_value(main_stack_outputs, "DockerBuildTemplate"),
        'Key': 'buildspec.yml'
    }
    s3 = boto3.resource('s3')

    bucket = s3.Bucket(dest_bucket)
    bucket.copy(copy_source, '.engine/buildspec.yml')


def handler(event, context):
    try:
        # algo_ID = fetch_algo_ID()
        params = json.loads(event['body'])
        algo_ID = params['id']

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error fetching algo ID: {e} "}),
        }

    try:
        
        ### ----- FETCH THIS SHIT HERE ----
        cf_outputs = get_stack_outputs(algo_ID)
        bucket_name = get_output_value(cf_outputs, "CodeBuildBucketName")

    except Exception as e:

        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error fetching stack resources: {e}"}),
        }
    try:
    
        s3 = boto3.client('s3')
        s3.put_object(Body=params["dockerfile"], Bucket=bucket_name, Key='.engine/dockerfile')
        s3.put_object(Body=params["app"], Bucket=bucket_name, Key='.engine/app.py')
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error dumping files {e}"}),
        }
    
    try:
        # COPY BUILDSPEC HERE
        copy_bucket(bucket_name)

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error copying template bucket: {e}"}),
        }

        

        

    try:
        cb = boto3.client('codebuild')
        project_name = get_output_value(cf_outputs, "DockerBuilderName")
        cb.start_build(projectName = project_name)

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error configuring docker image: {e}"}),
        }
    
    # Push dockerfile and app here
        
    response = {
            'statusCode': 200,
            'body': json.dumps({"message": f"Configuration started"})
        }
    return response
    