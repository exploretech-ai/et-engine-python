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


def handler(event, context):

    try:
        algoID = event['pathParameters']['algoID']

        # params = json.loads(event['body'])

        cf_outputs = get_stack_output(algoID)

        cluster_name = get_output_value(cf_outputs, "ClusterName")
        task_definition = get_output_value(cf_outputs, "TaskName").split('/')[-1]
        subnet_ids = get_output_value(cf_outputs, "PublicSubnetId")
        security_group_ids = get_output_value(cf_outputs, "SecurityGroupID")
        

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error fetching algorithm infrastructure: {e}")
        }

    # Executes an ECS task
    try:
        ecs_client = boto3.client('ecs')
        ecs_response = ecs_client.run_task(
            cluster=cluster_name,
            taskDefinition=task_definition,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [subnet_ids],
                    'securityGroups': [security_group_ids],
                    'assignPublicIp': 'ENABLED'
                }
            }
        )
        
        task_arn = ecs_response['tasks'][0]['taskArn']
        response = {
            'statusCode': 200,
            'body': json.dumps(f'Task started, ARN: {task_arn}')
        }

    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f'Error executing task: {e}')
        }


    return response