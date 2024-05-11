import boto3
import json    
import lambda_utils

def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']
        tool_id = event['pathParameters']['toolID']

        capacity_provider_name = "AsgCapacityProvider"

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

                if 'hardware' in body:
                    capacity_provider_name = body.pop('hardware')


                for key in body.keys():
                    args.append({
                        'name': key,
                        'value': body[key]
                    })

        print(f'Capacity Provider: {capacity_provider_name}')
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
        print('Registering Task')


        # use ecs_client.register_task_definition() to create a task definition
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/register_task_definition.html#
        task_def = ecs_client.register_task_definition(
            family="tool-" + tool_id,
            taskRoleArn="arn:aws:iam::734818840861:role/ETEngineAPI706397EC-ECSTaskRoleF2ADB362-6bXEZofBdhmg",
            executionRoleArn="arn:aws:iam::734818840861:role/ETEngineAPI706397EC-ECSTaskRoleF2ADB362-6bXEZofBdhmg",
            memory="512",
            containerDefinitions=[
                {
                    'name': "tool-" + tool_id + "-TEST",
                    'image': "734818840861.dkr.ecr.us-east-2.amazonaws.com/tool-" + tool_id + ':latest',
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-region': "us-east-2" ,
                            'awslogs-group': "EngineLogGroup"
                        }
                    },
                    'mountPoints': [
                        {
                            'sourceVolume': "efs",
                            "containerPath": '/data',
                            'readOnly': False
                        }
                    ]
                }
            ],
            volumes=[
                {
                    'name': "efs",
                    'efsVolumeConfiguration': {
                        "fileSystemId": "fs-0d876857100c16209",
                        "rootDirectory": "/",
                        "transitEncryption": "ENABLED",
                        "authorizationConfig": {
                            "accessPointId": "fsap-09a43eb7a30643436",
                            "iam": "ENABLED"
                        }
                    }
                }
            ]
        )
        print(task_def)

        task_arn = task_def['taskDefinition']['taskDefinitionArn']
        print("Running Task " + task_arn)


        # Run Task
        ecs_response = ecs_client.run_task(

            # This will be determined by the Hardware
            cluster="ETEngineAPI706397EC-ClusterEB0386A7-M0TrrRi5C32N",

            taskDefinition=task_arn,

            # Seems to be working fine 
            # launchType='EC2',

            capacityProviderStrategy=[
                {
                    'capacityProvider': capacity_provider_name
                },
            ],

            overrides={
                'containerOverrides': [
                    {
                        'name': f"tool-{tool_id}-TEST",
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