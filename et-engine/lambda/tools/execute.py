import boto3
import json    
import lambda_utils

def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']
        tool_id = event['pathParameters']['toolID']

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

        print(f'Arguments: {args}')


    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error processing task: {e}")
        }

    # Executes an ECS task
    try:
        ecs_client = boto3.client('ecs')

        # >>>>>
        print('Starting Task')
        ecs_response = ecs_client.run_task(

            # This will be determined by the Hardware
            cluster="ETEngineAPI706397EC-ClusterEB0386A7-M0TrrRi5C32N",

            taskDefinition="tool-" + tool_id,

            # Seems to be working fine 
            # launchType='EC2',

            capacityProviderStrategy=[
                {
                    'capacityProvider': 'AsgCapacityProvider'
                },
            ],


            overrides={
                'containerOverrides': [
                    {
                        'name': f"tool-{tool_id}",
                        'environment': args,
                    }
                ]
            }
        )
        print('SUCCESS!')
        # =====
        # ecs_response = ecs_client.run_task(
        #     cluster=components["ClusterName"],
        #     taskDefinition=components["TaskName"].split('/')[-1],
        #     launchType='FARGATE',
        #     networkConfiguration={
        #         'awsvpcConfiguration': {
        #             'subnets': [components["PublicSubnetId"]],
        #             'securityGroups': [components["SecurityGroupID"]],
        #             'assignPublicIp': 'ENABLED'
        #         }
        #     },
        #     overrides={
        #         'containerOverrides': [
        #             {
        #                 'name': f"tool-{tool_id}",
        #                 'environment': args,
        #             }
        #         ]
        #     }
        # )
        # <<<<<
        
        if len(ecs_response['tasks']) == 0:
            print(ecs_response)
            raise Exception('No task launched')
        
        task_arn = ecs_response['tasks'][0]['taskArn']
        response = {
            'statusCode': 200,
            'body': json.dumps(f'Task started, ARN: {task_arn}')
        }

    except Exception as e:
        print(f'Error executing task: {e}')
        response = {
            'statusCode': 500,
            'body': json.dumps('Task failed to launch')
        }


    return response