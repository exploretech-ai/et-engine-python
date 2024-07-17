import boto3
import json
import logging
import time
import os
import sys
import uuid

import job_utils

logging.basicConfig(stream=sys.stdout)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def submit_job(tool_id, request_id, user_id, body):
    """
    body has the following format:

        {
            'hardware': {}  (optional, if specified it must be JSON)
            '

        }
    """

    batch_parameters = job_utils.get_batch_parameters()
    role_arn = batch_parameters['role_arn']

    image = "734818840861.dkr.ecr.us-east-2.amazonaws.com/tool-" + tool_id + ':latest'
    container_mount_base = "/mnt/efs"
    args = []

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

    # connection = CONNECTION_POOL.getconn()
    # cursor = connection.cursor()
    try:
        batch_client = boto3.client('batch')
        mount_points = []
        volumes = []

        if hardware['filesystems']:
            for vfs_id in hardware['filesystems']:
                
                vfs_stack_outputs = job_utils.get_stack_outputs("vfs-"+vfs_id)
                file_system_id = job_utils.get_component_from_outputs(vfs_stack_outputs, "FileSystemId")
                access_point_id = job_utils.get_component_from_outputs(vfs_stack_outputs, "AccessPointId")

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

        # task_id = log_task(job_arn, user_id, tool_id, log_id, json.dumps(hardware), json.dumps(args), cursor)
        
        # connection.commit()

        return job_arn
        
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        # return Response('Task failed to launch', status=500)
    
    # finally:
    #     cursor.close()
    #     CONNECTION_POOL.putconn(connection)



def submit_batch(tool_id, request_id, user_id, fixed_args, varying_args):
    # for each in varying args:
    #     Construct "body" from fixed_args and this varying arg
    #     Run submit_job
    pass


if __name__ == "__main__":
    LOGGER.info("Starting Job Submission Loop")
    job_submission_queue_url = os.environ['JOB_SUBMISSION_QUEUE_URL']
    sqs = boto3.client('sqs')


    while True:
        
        LOGGER.info("Polling job submission queue")        
        try:

            sqs_resposne = sqs.receive_message(
                QueueUrl=job_submission_queue_url
            )

            message = sqs_resposne['Messages'][0]
            receipt_handle = message['ReceiptHandle']
            LOGGER.info("Found message")

            if message['Body']:
                args = json.loads(message['Body'])
                submission = args.pop("submission")

                user_id = submission['user_id']
                request_id = submission['request_id']
                tool_id = submission['tool_id']

                job_arn = submit_job(tool_id, request_id, user_id, args)
                LOGGER.info(job_arn)

                sqs.delete_message(
                    QueueUrl=job_submission_queue_url,
                    ReceiptHandle=receipt_handle
                )
    
            LOGGER.info("Message deleted")

        except KeyError as e:
            LOGGER.info("No messages found (Key Error)")

        except IndexError as e:
            LOGGER.info("No messages found (Index Error)")

        except Exception as e:
            LOGGER.exception(e)

        finally:
            time.sleep(5)