import lambda_utils
import uuid
import boto3


def handler(event, _context):

    capacity_provider_name = "AsgCapacityProvider"
    engine_stack_name = "ETEngine"
    
    print("UPLOAD REQUESTED")
    print(event)

    try:

        s3_bucket = event['Records'][0]['s3']['bucket']['name']
        s3_key = event['Records'][0]['s3']['object']['key']
        vfs_id = s3_bucket[4:]

        print('bucket: ', s3_bucket)
        print('key: ', s3_key)
        print('VFS Id:', vfs_id)

        vfs_name = "vfs-" + vfs_id
        container_mount_base = "/mnt/efs"
        mount_points = [{
            'sourceVolume': vfs_name,
            "containerPath": container_mount_base,
            'readOnly': False
        }]

        vfs_stack = lambda_utils.get_stack_outputs(vfs_name)
        file_system_id = lambda_utils.get_component_from_outputs(vfs_stack, "FileSystemId")
        access_point_id = lambda_utils.get_component_from_outputs(vfs_stack, "AccessPointId")

        engine_stack = lambda_utils.get_stack_outputs(engine_stack_name)
        cluster = lambda_utils.get_component_from_outputs(engine_stack, "ClusterName")
        image = lambda_utils.get_component_from_outputs(engine_stack, "UploadContainerUri")
        role_arn = lambda_utils.get_component_from_outputs(engine_stack, "UploadRoleArn")

        volumes = [{
            'name': vfs_name,
            'efsVolumeConfiguration': {
                "fileSystemId": file_system_id,
                "rootDirectory": "/",
                "transitEncryption": "ENABLED",
                "authorizationConfig": {
                    "accessPointId": access_point_id,
                    "iam": "ENABLED"
                }
            }
        }]

        args = [
            {
                "name": "s3_bucket",
                "value": s3_bucket
            },
            {
                "name": "s3_key",
                "value": s3_key
            },
            {
                "name": "volume_name",
                "value": vfs_name
            }
        ]

        log_id = str(uuid.uuid4())
        container_definition = {
            'name': "s3-to-efs-download",
            'image': image,
            'logConfiguration': {
                'logDriver': 'awslogs',
                'options': {
                    'awslogs-region': "us-east-2" ,
                    'awslogs-group': "EngineLogGroup",
                    "awslogs-stream-prefix": log_id
                }
            },
            'mountPoints': mount_points
        }

        ecs_client = boto3.client('ecs')
        task_def = ecs_client.register_task_definition(
            family="data-upload",
            taskRoleArn=role_arn,
            executionRoleArn=role_arn,
            containerDefinitions=[container_definition],
            volumes=volumes,
            memory="14GB",
            cpu="4vCPU"
        )
        print(f"Task Definition: {task_def}")
        
        task_arn = task_def['taskDefinition']['taskDefinitionArn']
        print("Task Definition ARN " + task_arn)
        
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
                        'name': "s3-to-efs-download",
                        'environment': args,
                    }
                ]
            }
        )
        print("ECS Launch Response:", ecs_response)

    except Exception as e:
        print("ERROR:", e)

    
    
