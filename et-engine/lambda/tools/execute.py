import boto3
import json    
import lambda_utils
import db


def fetch_available_vfs(user, cursor):
                    
    sql_query = f"""
        SELECT name, vfsID FROM VirtualFilesystems WHERE userID = '{user}'
    """
    cursor.execute(sql_query)
    available_vfs = cursor.fetchall()

    vfs_id_map = {}
    for row in available_vfs:
        vfs_id_map[row[0]] = row[1]
    
    return vfs_id_map


def handler(event, context):

    # Cluster Properties
    role_arn = "arn:aws:iam::734818840861:role/ETEngineAPI706397EC-ECSTaskRoleF2ADB362-6bXEZofBdhmg"
    cluster="ETEngineAPI706397EC-ClusterEB0386A7-M0TrrRi5C32N"
    

    try:
        user = event['requestContext']['authorizer']['userID']
        tool_id = event['pathParameters']['toolID']

        image = "734818840861.dkr.ecr.us-east-2.amazonaws.com/tool-" + tool_id + ':latest'
        container_mount_base = "/mnt/"
        args = []

        # This eventually gets replaced with something more dynamic
        capacity_provider_name = "AsgCapacityProvider"        
        
        # pass API key as environment variable if exists
        if "apiKey" in event['requestContext']['authorizer'].keys():
            args.append({
                'name': 'ET_ENGINE_API_KEY',
                'value': event['requestContext']['authorizer']['apiKey']
            })

        if 'body' in event:
            if event['body'] is not None:
                body = json.loads(event['body'])

                if 'hardware' in body:
                    hardware = body.pop('hardware')
                    hardware = json.loads(hardware)

                # Default Hardware
                else:
                    hardware = {
                        'filesystems': [],
                        'memory': 512,
                        'cpu': 1,
                        'gpu': False
                    }

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

        print('Registering Task')

        mount_points = []
        volumes = []

        if hardware['filesystems']:
            print("VFS MOUNT REQUESTED")

            vfs_id_map = fetch_available_vfs(user, cursor)

            for vfs_name in hardware['filesystems']:
                
                print(f'> mounting {vfs_name}')

                vfs_id = vfs_id_map[vfs_name]
                vfs_stack_outputs = lambda_utils.get_stack_outputs("vfs-"+vfs_id)
                file_system_id = lambda_utils.get_component_from_outputs(vfs_stack_outputs, "FileSystemId")
                access_point_id = lambda_utils.get_component_from_outputs(vfs_stack_outputs, "AccessPointId")

                volume_name = "vfs-" + vfs_id
                mount_points.append(
                    {
                        'sourceVolume': volume_name,
                        "containerPath": container_mount_base + vfs_id,
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
        print(f'Mount Points: {mount_points}')
        print(f'Volumes: {volumes}')

        print('DEFINING CONTAINER')
        container_definition = {
            'name': "tool-" + tool_id,
            'image': image,
            'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                    'awslogs-region': "us-east-2" ,
                    'awslogs-group': "EngineLogGroup"
                }
            },
            'mountPoints': mount_points,
            'memory': hardware['memory'],
            'cpu': hardware['cpu'],
        }
        if hardware['gpu']:
            print('ADDING GPU')
            container_definition['resourceRequirements'] = [
                {
                    'value': hardware['gpu'],
                    'type': 'GPU'
                }
            ]
        print(f'Container Definition: {container_definition}')
    
        print('REGISTERING TASK DEFINITION')
        task_def = ecs_client.register_task_definition(
            family="tool-" + tool_id,
            taskRoleArn=role_arn,
            executionRoleArn=role_arn,
            containerDefinitions=[container_definition],
            volumes=volumes
        )
        print(f"Task Definition: {task_def}")

        task_arn = task_def['taskDefinition']['taskDefinitionArn']
        print("Task Definition ARN " + task_arn)

        print('RUNNING TASK')
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
                        'name': "tool-" + tool_id,
                        'environment': args,
                    }
                ]
            }
        )
        print('Task Successfully Submitted')
        
        if len(ecs_response['tasks']) == 0:
            print(ecs_response)
            raise Exception('No task launched')
        
        task_arn = ecs_response['tasks'][0]['taskArn']
        return {
            'statusCode': 200,
            'body': json.dumps(f'Task started, ARN: {task_arn}')
        }

    except Exception as e:
        print(f'Error executing task: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps('Task failed to launch')
        }
    
    finally:
        cursor.close()
        connection.close()
    