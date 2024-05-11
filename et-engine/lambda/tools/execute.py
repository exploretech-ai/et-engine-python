import boto3
import json    
import lambda_utils
import db

def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']
        tool_id = event['pathParameters']['toolID']

        # Defaults
        capacity_provider_name = "AsgCapacityProvider"
        vfs_name = False

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

                if 'vfs_name' in body:
                    vfs_name = body.pop('vfs_name')

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
    connection = db.connect()
    cursor = connection.cursor()
    try:
        ecs_client = boto3.client('ecs')

        # >>>>>
        print('Registering Task')
        container_mount_point = "/data"
        container_name = "tool-" + tool_id + "-TEST"

        mount_points = []
        volumes = []
        volume_number = 1

        if vfs_name:
            print("VFS MOUNT REQUESTED")


            sql_query = f"""
                SELECT name, vfsID FROM VirtualFilesystems WHERE userID = '{user}'
            """
            cursor.execute(sql_query)
            available_vfs = cursor.fetchall()
            print(available_vfs)
            vfs_id_map = {}
            for row in available_vfs:
                print(row)
                vfs_id_map[row[0]] = row[1]
            print(vfs_id_map)
            vfs_id = vfs_id_map[vfs_name]
            print(vfs_name, vfs_id)

            vfs_stack_outputs = lambda_utils.get_stack_outputs("vfs-"+vfs_id)
            print(vfs_stack_outputs)
            file_system_id = lambda_utils.get_component_from_outputs(vfs_stack_outputs, "FileSystemId")
            access_point_id = lambda_utils.get_component_from_outputs(vfs_stack_outputs, "AccessPointId")


            volume_name = "vol" + str(volume_number)
            print(file_system_id, access_point_id, volume_name)
            mount_points.append(
                {
                    'sourceVolume': volume_name,
                    "containerPath": container_mount_point,
                    'readOnly': False
                }
            )
            volumes.append(
                {
                    'name': volume_name,
                    'efsVolumeConfiguration': {
                        "fileSystemId": file_system_id,
                        "rootDirectory": "/",
                        "transitEncryption": "ENABLED",
                        "authorizationConfig": {
                            "accessPointId": access_point_id,
                            "iam": "ENABLED"
                        }
                    }
                }
            )
            volume_number += 1
        print(mount_points, volumes)


        # volume_name = "efs"
        # file_system_id = "fs-055040c5bf7d34d30"
        # access_point_id = "fsap-0c130b5a9e4235026"
        

        role_arn = "arn:aws:iam::734818840861:role/ETEngineAPI706397EC-ECSTaskRoleF2ADB362-6bXEZofBdhmg"
        memory = "512"

        image = "734818840861.dkr.ecr.us-east-2.amazonaws.com/tool-" + tool_id + ':latest'
        cluster="ETEngineAPI706397EC-ClusterEB0386A7-M0TrrRi5C32N"

        # EACH VFS GETS:
        # 1. Mount Point in container
        # 2. Volume in Task Definition

        # Create a task definition
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs/client/register_task_definition.html#
        task_def = ecs_client.register_task_definition(
            family="tool-" + tool_id,
            taskRoleArn=role_arn,
            executionRoleArn=role_arn,
            memory=memory,
            containerDefinitions=[
                {
                    'name': container_name,
                    'image': image,
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-region': "us-east-2" ,
                            'awslogs-group': "EngineLogGroup"
                        }
                    },
                    'mountPoints': mount_points
                }
            ],
            volumes=volumes
        )
        print(task_def)

        task_arn = task_def['taskDefinition']['taskDefinitionArn']
        print("Running Task " + task_arn)


        # Run Task
        ecs_response = ecs_client.run_task(
            cluster=cluster,
            taskDefinition=task_arn,
            capacityProviderStrategy=[
                {
                    'capacityProvider': capacity_provider_name
                },
            ],
            overrides={
                'containerOverrides': [
                    {
                        'name': container_name,
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