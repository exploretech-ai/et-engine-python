import boto3
import json

def handler(event, context):
    cluster_name = 'engine-cfn-3246a962a4994e08a17c49df26d5fb6e-ECSCluster-YLS1aBWEtTmH'
    task_definition = 'engine-cfn-3246a962a4994e08a17c49df26d5fb6e-ECSTaskDefinition-c92sqD91heAT'
    subnet_ids = ['subnet-041bc9485dcf5d81b']  # Replace with your subnet IDs
    security_group_ids = ['sg-03f00b00130f3e38b']  # Replace with your security group IDs




    # Executes an ECS task
    

    try:
        ecs_client = boto3.client('ecs')
        ecs_response = ecs_client.run_task(
            cluster=cluster_name,
            taskDefinition=task_definition,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnet_ids,
                    'securityGroups': security_group_ids,
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