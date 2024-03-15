import boto3
import json    
import lambda_utils

def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']

        # vfsID as a path parameter
        tool_id = event['pathParameters']['toolID'] 

        # check if vfsID exists under user
        available_tools = lambda_utils.list_tools(user)
        tool_name = lambda_utils.get_tool_name(user, tool_id)
        if tool_name not in available_tools:
            return {
                'statusCode': 403,
                'body': json.dumps('Tool unavailable')
            }


        components = lambda_utils.get_tool_components(tool_id, 
            [
                "ClusterName", 
                "TaskName", 
                "PublicSubnetId", 
                "SecurityGroupID"
            ]
        )

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error processing task: {e}")
        }

    # Executes an ECS task
    try:
        ecs_client = boto3.client('ecs')
        ecs_response = ecs_client.run_task(
            cluster=components["ClusterName"],
            taskDefinition=components["TaskName"].split('/')[-1],
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [components["PublicSubnetId"]],
                    'securityGroups': [components["SecurityGroupID"]],
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