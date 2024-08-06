import boto3
import json
import logging
import time
import os
import sys
import uuid
import psycopg2

from config import initialize
import job_utils


class NoMessageFoundError(Exception):
    pass

class InvalidMessageFormat(Exception):
    pass


logging.basicConfig(stream=sys.stdout)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

CONNECTION_PARAMS, JOB_SUBMISSION_QUEUE_URL = initialize()


def create_job_definition(batch_client, hardware):
    batch_parameters = job_utils.get_batch_parameters()
    role_arn = batch_parameters['role_arn']

    image = "734818840861.dkr.ecr.us-east-2.amazonaws.com/tool-" + tool_id + ':latest'
    container_mount_base = "/mnt/efs"

    mount_points = []
    volumes = []

    if hardware['filesystems']:
        for vfs_id in hardware['filesystems']:
            
            engine_outputs = job_utils.get_stack_outputs("ETEngine")
            file_system_id = job_utils.get_component_from_outputs(engine_outputs, "MasterFileSystemId")
            
            vfs_stack_outputs = job_utils.get_stack_outputs("vfs-"+vfs_id)
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
                        # "rootDirectory": "/",
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

    return job_definition['jobDefinitionArn'], log_id


def submit_job(tool_id, batch_id, log_id, args, batch_client, job_definition_arn):
    """
    https://docs.exploretech.ai/et-engine/tool_methods.html#base.tool_methods.submit_monte_carlo 
    """

    try:

        batch_response = batch_client.submit_job(
            jobName='tool-'+tool_id+"-"+str(uuid.uuid4()),
            jobQueue="JobQueueEE3AD499-ykz4wxsfUYiw86fC",
            jobDefinition=job_definition_arn,
            containerOverrides={
                'environment': args
            }
        )

        job_arn = batch_response['jobArn']
        job_id = batch_response['jobId']
        return (job_id, job_arn, batch_id, log_id, json.dumps(args))
        
    except Exception as e:
        LOGGER.exception(f"[{batch_id}]")


def submit_batch(tool_id, batch_id, fixed_args, variable_args, hardware, batch_client):

    job_definition_arn, log_id = create_job_definition(batch_client, hardware)

    batch_jobs = []
    for individual_args in variable_args:
        
        job_args = []
        for key in fixed_args.keys():
            job_args.append({
                'name': key,
                'value': fixed_args[key]
            })
        for key in individual_args.keys():
            job_args.append({
                'name': key,
                'value': individual_args[key]
            })

        job = submit_job(tool_id, batch_id, log_id, job_args, batch_client, job_definition_arn)
        batch_jobs.append(job)
        
    return batch_jobs


def submit_single_job_batch(tool_id, batch_id, fixed_args, hardware, batch_client):

    args = []
    for key in fixed_args.keys():
        args.append({
            'name': key,
            'value': fixed_args[key]
        })

    job_definition_arn, log_id = create_job_definition(batch_client, hardware)
    job = submit_job(tool_id, batch_id, log_id, args, batch_client, job_definition_arn)

    return [job]


if __name__ == "__main__":
    
    LOGGER.info("Starting Job Submission Loop")

    sqs_client = boto3.client('sqs')
    batch_client = boto3.client('batch')

    while True:
        
        LOGGER.info("Polling job submission queue")        
        connection = psycopg2.connect(**CONNECTION_PARAMS)
        cursor = connection.cursor()
        try:

            sqs_resposne = sqs_client.receive_message(
                QueueUrl=JOB_SUBMISSION_QUEUE_URL
            )

            if not 'Messages' in sqs_resposne:
                raise NoMessageFoundError
            
            message = sqs_resposne['Messages'][0]
            receipt_handle = message['ReceiptHandle']
            LOGGER.info("Found message")

            sqs_client.delete_message(
                QueueUrl=JOB_SUBMISSION_QUEUE_URL,
                ReceiptHandle=receipt_handle
            )
            LOGGER.info("Deleted message")

            if not message['Body']:
                raise           

            body = json.loads(message['Body']) 

            submission = body.pop("submission")
            fixed_args = body.pop("fixed_args")
            variable_args = body.pop("variable_args")
            hardware = body.pop("hardware")

            batch_id = submission['batch_id']
            tool_id = submission['tool_id']

            if variable_args:
                jobs = submit_batch(tool_id, batch_id, fixed_args, variable_args, hardware, batch_client)
            else:
                jobs = submit_single_job_batch(tool_id, batch_id, fixed_args, hardware, batch_client)
                

            # Insert into database
            row_values = ','.join(cursor.mogrify("(%s,%s,%s,%s,%s)", row).decode("utf-8") for row in jobs)
            LOGGER.info(row_values)
            cursor.execute(
                """
                INSERT INTO Jobs (jobID, jobArn, batchID, logID, args) VALUES 
                """ + row_values
            )
            connection.commit()

            LOGGER.info(f"Submitted {len(jobs)} job(s)")


        except KeyError as e:
            LOGGER.exception(e)

        except NoMessageFoundError:
            LOGGER.info("No messages found")

        except Exception as e:
            LOGGER.exception(e)

        finally:
            cursor.close()
            connection.close()
            time.sleep(5)