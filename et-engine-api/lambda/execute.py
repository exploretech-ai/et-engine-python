import boto3
import json    
from databases import get_stack_outputs, get_output_value



def handler(event, context):

    try:

        params = json.loads(event['body'])
        algo_ID = params['id']

        cf_outputs = get_stack_outputs(algo_ID)

        cluster_name = get_output_value(cf_outputs, "ClusterName")
        task_definition = get_output_value(cf_outputs, "TaskName").split('/')[-1]
        # subnet_ids = get_output_value(cf_outputs, "SubnetID")
        # security_group_ids = get_output_value(cf_outputs, "SecurityGroupID")
        
        subnet_ids = "subnet-06f7655a729b6c494"
        security_group_ids = "sg-07dfca753315715a2" 

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