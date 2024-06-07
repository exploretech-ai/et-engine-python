import boto3
import json    
import lambda_utils
import db
import uuid
import datetime

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


def log_task(task_arn, user_id, tool_id, log_id, hardware, args, cursor):

    start_time = datetime.datetime.now()
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    status="SUBMITTED"
    status_time = datetime.datetime.now()
    status_time = status_time.strftime('%Y-%m-%d %H:%M:%S')

    task_id = str(uuid.uuid4())

    print('hardware: ', hardware)
    print('args: ', args)

    query = f"""
        INSERT INTO Tasks (taskID, taskArn, userID, toolID, logID, start_time, hardware, status, status_time, args)
        VALUES ('{task_id}', '{task_arn}', '{user_id}', '{tool_id}', '{log_id}', '{start_time}', '{hardware}', '{status}', '{status_time}', '{args}')
    """
    print(query)
    cursor.execute(query)
    
    return task_id
    

def handler(event, context):

    # Cluster Properties
    role_arn = "arn:aws:iam::734818840861:role/ETEngineAPI706397EC-ECSTaskRoleF2ADB362-6bXEZofBdhmg"
    cluster="ETEngineAPI706397EC-ClusterEB0386A7-M0TrrRi5C32N"
    
    try:
        user = event['requestContext']['authorizer']['userID']
        tool_id = event['pathParameters']['toolID']

        print(f'Execute Requested on Tool {tool_id}')

        image = "734818840861.dkr.ecr.us-east-2.amazonaws.com/tool-" + tool_id + ':latest'
        container_mount_base = "/mnt/"
        args = []

        # This eventually gets replaced with something more dynamic
        capacity_provider_name = "AsgCapacityProvider"        
        
        # pass API key as environment variable if exists
        if "apiKey" in event['requestContext']['authorizer'].keys():
            print('API Key found... copying to environment variable')
            args.append({
                "name": "ET_ENGINE_API_KEY",
                "value": event['requestContext']['authorizer']['apiKey']
            })

        if 'body' in event:
            print(f'Request body: {event["body"]}')

            if event['body'] is not None:
                body = json.loads(event['body'])

                if 'hardware' in body:
                    hardware = body.pop('hardware')

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
        print(f'Hardware: {hardware}')
        print(f'Arguments: {args}')


    except Exception as e:
        print(f"Error processing task: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Error parsing task parameters')
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
        log_id = str(uuid.uuid4())
        container_definition = {
            'name': "tool-" + tool_id,
            'image': image,
            'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                    'awslogs-region': "us-east-2" ,
                    'awslogs-group': "EngineLogGroup",
                    "awslogs-stream-prefix": log_id
                }
            },
            'mountPoints': mount_points,
            # 'memory': hardware['memory'],
            # 'cpu': hardware['cpu'],
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
            volumes=volumes,
            memory=str(hardware['memory']),
            cpu=str(hardware['cpu'])
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
        if len(ecs_response['tasks']) == 0:
            print(ecs_response)
            raise Exception('No task launched')
        
        print('Task Successfully Submitted')
        print('Logging Task...')

        # task_id = str(uuid.uuid4())
        print('ECS response: ', ecs_response)

        task = ecs_response['tasks'][0]
        print('Task: ', task)

        task_arn = task['taskArn']
        print('Task Arn: ', task_arn)

        args.pop(0)
        task_id = log_task(task_arn, user, tool_id, log_id, json.dumps(hardware), json.dumps(args), cursor)
        print('Executed query, waiting to commit...')

        connection.commit()
        print('committed')

        print('Task ID: ', task_id)
        
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(task_id)
        }

    except Exception as e:
        print(f'Error executing task: {e}')
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Task failed to launch')
        }
    
    finally:
        cursor.close()
        connection.close()
    