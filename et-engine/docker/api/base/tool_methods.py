from flask import Blueprint, Response, request
import json
import uuid
import datetime
import time
import boto3
from . import utils
from . import CONNECTION_POOL, LOGGER, JOB_SUBMISSION_QUEUE_URL


tools = Blueprint('tools', __name__)


@tools.route('/tools', methods=['GET'])
def list_tools():

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            SELECT name, toolID FROM Tools WHERE userID = %s
            """,
            (user_id,)
        )
        available_tools = cursor.fetchall()

        cursor.execute(
            """
            SELECT 
                name, toolID 
            FROM
                Tools
            INNER JOIN Sharing
                ON Tools.toolID = Sharing.resourceID AND Sharing.resource_type = 'tools' AND Sharing.granteeID = %s
            """,
            (user_id,)
        )
        shared_tools = cursor.fetchall()

        for tool in available_tools:
            tool = tool + ("owned",)
        for tool in shared_tools:
            tool = tool + ("shared",)

        available_tools.extend(shared_tools)
        payload = json.dumps(available_tools)
        return Response(payload, status=200)

    except:
        return Response("Unknown error occurred", status=500)

    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)

    
@tools.route('/tools', methods=['POST'])
def create_tool():

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)

    except Exception as e:
        return Response("Error parsing request body", status=400)

    try:
        tool_name = body['name']
        tool_description = body['description']
    
    except KeyError as e:
        return Response("Request missing name or description", status=400)
    
    except Exception as e:
        return Response("Error parsing request body", status=400)

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            SELECT name FROM Tools WHERE userID = %s
            """,
            (user_id,)
        )
        available_tools = [row[0] for row in cursor.fetchall()]

        if tool_name in available_tools:
            return Response(f"Failed: '{tool_name}' already exists", status=409)
        
        tool_id = str(uuid.uuid4())
        cfn = boto3.client('cloudformation')

        parameters = [
            {
                'ParameterKey': 'toolID',
                'ParameterValue': tool_id
            },
        ]
        
        cfn.create_stack(
            StackName='tool-' + tool_id,
            TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/compute-basic.yaml',
            Parameters=parameters,
            Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
        )

        cursor.execute(
            """
            INSERT INTO Tools (toolID, userID, name, description)
            VALUES (%s, %s, %s, %s)
            """,
            (tool_id, user_id, tool_name, tool_description)
        )
        connection.commit()
        return Response(status=200)
        
    except:
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@tools.route('/tools/<tool_id>', methods=['GET'])
def describe_tool(tool_id):

    try:
        tool_is_ready = utils.check_ecr(tool_id)
        build_status = utils.check_codebuild(tool_id)
        tool_parameters = json.dumps({
            'ready': tool_is_ready,
            'buildStatus': build_status
        })
        return Response(tool_parameters, status=200)
    
    except:
        return Response("Unknown error occurred", status=500)        


@tools.route('/tools/<tool_id>', methods=['POST'])
def execute_tool(tool_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context['request_id']

    cluster_parameters = utils.get_cluster_parameters()
    role_arn = cluster_parameters['role_arn']
    cluster_name = cluster_parameters['cluster_name']
    capacity_provider_name = cluster_parameters['capacity_provider_name']

    image = "734818840861.dkr.ecr.us-east-2.amazonaws.com/tool-" + tool_id + ':latest'
    container_mount_base = "/mnt/efs"
    args = []

    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)

    except Exception as e:
        return Response("Error parsing request body", status=400)

    if 'hardware' in body:
        hardware = body.pop('hardware')

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

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:
        ecs_client = boto3.client('ecs')
        mount_points = []
        volumes = []

        if hardware['filesystems']:
            vfs_id_map = fetch_available_vfs(user_id, cursor)
            for vfs_name in hardware['filesystems']:
                
                vfs_id = vfs_id_map[vfs_name]
                vfs_stack_outputs = utils.get_stack_outputs("vfs-"+vfs_id)
                file_system_id = utils.get_component_from_outputs(vfs_stack_outputs, "FileSystemId")
                access_point_id = utils.get_component_from_outputs(vfs_stack_outputs, "AccessPointId")

                volume_name = "vfs-" + vfs_id
                mount_points.append(
                    {
                        'sourceVolume': volume_name,
                        "containerPath": container_mount_base,
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
            container_definition['resourceRequirements'] = [
                {
                    'value': hardware['gpu'],
                    'type': 'GPU'
                }
            ]

        task_def = ecs_client.register_task_definition(
            family="tool-" + tool_id,
            taskRoleArn=role_arn,
            executionRoleArn=role_arn,
            containerDefinitions=[container_definition],
            volumes=volumes,
            memory=str(hardware['memory']),
            cpu=str(hardware['cpu'])
        )

        task_arn = task_def['taskDefinition']['taskDefinitionArn']
        
        ecs_response = ecs_client.run_task(
            cluster=cluster_name,
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
            raise
        
        task = ecs_response['tasks'][0]
        task_arn = task['taskArn']
        if args:
            args.pop(0)
        task_id = log_task(task_arn, user_id, tool_id, log_id, json.dumps(hardware), json.dumps(args), cursor)
        
        connection.commit()

        return Response(task_id, status=200)
        
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response('Task failed to launch', status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)

    
@tools.route('/tools/<tool_id>', methods=['PUT'])
def build_tool(tool_id):

    try:
        s3 = boto3.client('s3')
        bucket_name = "tool-" + tool_id
        presigned_post = s3.generate_presigned_post(
            bucket_name, 
            "tool.zip",
            ExpiresIn=60
        )    
        return Response(json.dumps(presigned_post), status=200)
    
    except Exception as e:
        return Response("Unknown error occurred", status=500)


@tools.route('/tools/<tool_id>', methods=['DELETE'])
def delete_tool(tool_id):
    
    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    is_owned = context['is_owned']

    if not is_owned:
        return Response('Must be owner to delete', status=403)

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            DELETE FROM Tools WHERE userID = %s AND toolID = %s
            """,
            (user_id, tool_id)
        )
        
        utils.empty_bucket("tool-"+tool_id)
        utils.delete_repository("tool-"+tool_id)
        utils.delete_stack("tool-"+tool_id)
        connection.commit()

        return Response(status=200)
    
    except:
        return Response("Unknown error occurred", status=500)

    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@tools.route('/tools/<tool_id>/share', methods=['POST'])
def share_tool(tool_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    is_owned = context['is_owned']

    if not is_owned:
        return Response('Must be owner to share', status=403)
    
    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)
    
    except KeyError as e:
        return Response("Request missing body", status=400)

    except Exception as e:
        return Response("Error parsing request body", status=400)
    
    if 'grantee' in body:
        grantee_id = body['grantee']
    else:
        return Response('Request body has no grantee', status=400)


    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:
        
        # throws an error if poorly-formed UUID
        uuid.UUID(grantee_id, version=4)
        
        accessID = str(uuid.uuid4())
        date_created = datetime.datetime.now()
        date_created = date_created.strftime('%Y-%m-%d %H:%M:%S')

        if user_id == grantee_id:
            return Response("Cannot share with yourself", status=403)
        
        cursor.execute(
            "SELECT * FROM Sharing WHERE ownerID = %s AND granteeID = %s AND resource_type = %s AND resourceID = %s",
            (user_id, grantee_id, "tools", tool_id)
        )
        if cursor.rowcount > 0:
            return Response("Already shared with this user", status=409)
        
        cursor.execute(
            """
            INSERT INTO Sharing (accessID, ownerID, granteeID, resource_type, resourceID, date_granted)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, 
            (
                accessID, 
                user_id, 
                grantee_id, 
                "tools", 
                tool_id, 
                date_created,
            )
        )
        connection.commit()

        return Response(status=200)

    except ValueError as e:
        return Response("Invalid grantee", status=400)
        
    except Exception as e:
        return Response("Unknown error", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@tools.route('/tools/<tool_id>/batch', methods=['POST'])
def submit_job(tool_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context['request_id']

    batch_parameters = utils.get_batch_parameters()
    role_arn = batch_parameters['role_arn']

    image = "734818840861.dkr.ecr.us-east-2.amazonaws.com/tool-" + tool_id + ':latest'
    container_mount_base = "/mnt/efs"
    args = []

    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)

    except Exception as e:
        return Response("Error parsing request body", status=400)

    if 'hardware' in body:
        hardware = body.pop('hardware')

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

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:
        batch_client = boto3.client('batch')
        mount_points = []
        volumes = []

        if hardware['filesystems']:
            vfs_id_map = fetch_available_vfs(user_id, cursor)
            for vfs_name in hardware['filesystems']:
                
                vfs_id = vfs_id_map[vfs_name]
                vfs_stack_outputs = utils.get_stack_outputs("vfs-"+vfs_id)
                file_system_id = utils.get_component_from_outputs(vfs_stack_outputs, "FileSystemId")
                access_point_id = utils.get_component_from_outputs(vfs_stack_outputs, "AccessPointId")

                volume_name = "vfs-" + vfs_id
                mount_points.append(
                    {
                        'sourceVolume': volume_name,
                        'containerPath': container_mount_base,
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
    
        log_id = str(uuid.uuid4())

        job_definition = batch_client.register_job_definition(
            jobDefinitionName=log_id,
            type='container',
            containerProperties={
                'image': image,
                'vcpus': hardware['cpu'],
                'memory': hardware['memory'],
                'jobRoleArn': role_arn,
                'executionRoleArn': role_arn,
                'volumes': volumes,
                'environment': args,
                'mountPoints': mount_points,
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-region': "us-east-2" ,
                        'awslogs-group': "EngineLogGroup",
                        "awslogs-stream-prefix": log_id
                    }
                }
            }
        )
        job_definition_arn = job_definition['jobDefinitionArn']
        batch_response = batch_client.submit_job(
            jobName='tool-'+tool_id+"-"+log_id,
            jobQueue="JobQueueEE3AD499-ykz4wxsfUYiw86fC",
            jobDefinition=job_definition_arn
        )

        job_arn = batch_response['jobArn']
        if args:
            args.pop(0)
        task_id = log_task(job_arn, user_id, tool_id, log_id, json.dumps(hardware), json.dumps(args), cursor)
        
        # connection.commit()

        return Response(task_id, status=200)
        
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response('Task failed to launch', status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@tools.route('/tools/<tool_id>/mc', methods=['POST'])
def submit_monte_carlo(tool_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context['request_id']

    try:
        message = request.get_data(as_text=True)
        message_dict = json.loads(message)
        message_dict['submission'] = {
            'user_id': user_id,
            'request_id': request_id,
            'tool_id': tool_id
        }
        
        sqs = boto3.client('sqs')
        sqs.send_message(
            QueueUrl=JOB_SUBMISSION_QUEUE_URL,
            MessageBody=json.dumps(message_dict),
            MessageGroupId=str(uuid.uuid4()),
            MessageDeduplicationId=str(uuid.uuid4())
        )

        return Response(status=200)

        
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response('Task failed to launch', status=500)
    

def fetch_available_vfs(user, cursor):
                    
    query = f"""
        SELECT name, vfsID FROM VirtualFilesystems WHERE userID = '{user}'
    """

    cursor.execute(query)
    available_vfs = cursor.fetchall()

    query = """
        SELECT 
            name, vfsID 
        FROM
            VirtualFileSystems
        INNER JOIN Sharing
            ON VirtualFileSystems.vfsID = Sharing.resourceID AND Sharing.resource_type = 'vfs' AND Sharing.granteeID = %s
    """
    cursor.execute(query, (user,))
    shared_vfs = cursor.fetchall()

    available_vfs.extend(shared_vfs)

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

    cursor.execute("""
        INSERT INTO Tasks (taskID, taskArn, userID, toolID, logID, start_time, hardware, status, status_time, args)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        task_id,
        task_arn,
        user_id,
        tool_id,
        log_id,
        start_time,
        hardware,
        status,
        status_time,
        args
    ))

    return task_id
    
