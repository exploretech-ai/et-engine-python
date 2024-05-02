import boto3
import json    
import lambda_utils

def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']

        # vfsID as a path parameter
        tool_id = event['pathParameters']['toolID']
        # id_token =  event['headers']['Authorization'].split(' ')[1]

        # check if 'key' exists in the body
        args = []
        if "apiKey" in event['requestContext']['authorizer'].keys():
            args.append({
                'name': 'ET_ENGINE_API_KEY',
                'value': event['requestContext']['authorizer']['apiKey']
            })

        if 'body' in event:
            if event['body'] is not None:
                body = json.loads(event['body'])
                for key in body.keys():
                    args.append({
                        'name': key,
                        'value': body[key]
                    })

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
            },
            overrides={
                'containerOverrides': [
                    {
                        'name': f"tool-{tool_id}",
                        'environment': args,
                    }
                ]
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