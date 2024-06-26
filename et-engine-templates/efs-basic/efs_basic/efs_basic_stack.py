from aws_cdk import (
    Stack,
    CfnOutput,
    CfnParameter,
    Duration,
    RemovalPolicy,
    aws_efs as efs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_autoscaling as autoscaling,
    aws_ecs as ecs,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
)
from constructs import Construct

list_lambda_code = """
import os
import base64
import math
import json
import boto3
import shutil


def delete(event):

    file_path = event['file']
    print(f"file_path={file_path}")

    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            raise OSError('path is neither file nor directory')
    except OSError:
        return {"message": "couldn't delete the file", "statusCode": 500}
    else:
        return {"message": "file deletion successful", "statusCode": 200}


def make_dir(event):
    path = event['path']
    print(f"path={path}")

    try:
        os.mkdir(path)
    except OSError:
        return {"message": "couldn't create the directory", "statusCode": 500}
    else:
        return {"message": "directory creation successful", "statusCode": 200}


def upload(event):
    print("UPLOAD REQUESTED")
    print(event)

    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_key = event['Records'][0]['s3']['object']['key']

    print('bucket: ', s3_bucket)
    print('key: ', s3_key)

    # Set the download path in the /tmp directory
    # download_path = '/tmp/' + os.path.basename(s3_key)
    destination_path = '/mnt/efs/' + s3_key[2:]
    # print('local path: ', download_path)

    # Create an S3 client
    s3_client = boto3.client('s3')

    try:
        # Download the file from S3
        print('Dowloading...')
        s3_client.download_file(s3_bucket, s3_key, destination_path)
        print(f"success")
        return {'message': 'successfully transfered file to EFS', 'statusCode': 200}
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return {'message': 'failed while downloading file to EFS', 'statusCode': 500}

          
def download(event):

    print('DOWNlOAD REQUESTED')

    try:
        key = event['key']
        prefix = event['prefix']
        bucket_name = event['vfs']

        print(f"key: {key}")
        print(f"prefix: {prefix}")
        print(f"bucket_name: {bucket_name}")

        file = prefix + key

        # Copy file to s3
        s3_client = boto3.client('s3')
        s3_client.upload_file(file, bucket_name, key)

        # Create presigned GET
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=60
        )
        return {'presigned_url': presigned_url, 'statusCode': 200}
    except KeyError as e:
        return {'presigned_url': 'KEY_ERROR', 'statusCode': 500}
    except Exception as e:
        print(f"Exception: {e}")
        return {'presigned_url': 'UNKNOWN EXCEPTION', 'statusCode': 500}


def list(path):
    
    try:
        dir_items = []
        file_items = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            dir_items.extend(dirnames)
            file_items.extend(filenames)
            break
        print("directories: ", dir_items)
        print("files: ", file_items)

    except Exception as error:
        print(error)
        return {"message": "unable to list files", "statusCode": 500}
    else:
        return {"path": path, "directories": dir_items, "files": file_items, "statusCode": 200}


def handler(event, _context):
    try:
        if "Records" in event:
            operation_type = "upload"
            path = None
        else:
            operation_type = event['operation']
            
    except KeyError:
        return {"message": "missing required parameter: operation", "statusCode": 400}
    else:
        print("Operation Type: ", operation_type)
        if operation_type == 'upload':
            upload_result = upload(event)
            return upload_result
        if operation_type == 'list':
            path = event['path']
            list_result = list(path)
            return list_result
        if operation_type == 'delete':
            delete_result = delete(event)
            return delete_result
        if operation_type == 'mkdir':
            make_dir_result = make_dir(event)
            return make_dir_result
        if operation_type == 'download':
            download_result = download(event)
            return download_result
        """

class EfsBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vfs_id = CfnParameter(
            self,
            "vfsID"
        ).value_as_string
        security_group_id = "sg-08ad2fb3a42e5ce01"
        vpc_id = "vpc-05c602ef885d449bc"

        vpc = ec2.Vpc.from_lookup(
            self,
            "ClusterVpc",
            vpc_id = vpc_id
        )
        security_group = ec2.SecurityGroup.from_security_group_id(
            self,
            "ClusterSG2",
            security_group_id = security_group_id
        )


        file_system = efs.FileSystem(
            self,
            "vfs",
            vpc = vpc,
            security_group=security_group,
            file_system_name = "vfs-" + vfs_id
        )
        file_system.add_to_resource_policy(
            iam.PolicyStatement(
                actions = ["elasticfilesystem:*"],
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()]
            )
        )
        access_point = file_system.add_access_point(
            "vfsAccessPoint",
            path="/",
            create_acl=efs.Acl(
                owner_gid="0",
                owner_uid="0",
                permissions="777"
            ),
            posix_user=efs.PosixUser(
                uid="0",
                gid="0"
            )
        )
        
        list_lambda_function = _lambda.Function(
            self,
            "VFSLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "index.handler",
            code=_lambda.Code.from_inline(list_lambda_code),
            timeout = Duration.minutes(15),
            vpc=vpc,
            function_name = "vfs-" + vfs_id,
            filesystem = _lambda.FileSystem.from_efs_access_point(
                access_point,
                "/mnt/efs"
            ),
        )

        upload_bucket = s3.Bucket(
            self,
            "UploadBucket",
            auto_delete_objects = True,
            removal_policy=RemovalPolicy.DESTROY,
            bucket_name = "vfs-" + vfs_id,
            lifecycle_rules=[
                s3.LifecycleRule(
                    expiration=Duration.days(1)
                )
            ]
        )
        upload_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, 
            s3n.LambdaDestination(list_lambda_function),
            s3.NotificationKeyFilter(
                prefix="./"
            )
        )
        list_lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*'
                ],
                resources=[
                    upload_bucket.bucket_arn,
                    upload_bucket.bucket_arn + "/*"
                ]
            )
        )
        upload_bucket.add_cors_rule(
            allowed_origins=["*"],
            allowed_methods=[
                s3.HttpMethods.PUT,
                s3.HttpMethods.POST,
                s3.HttpMethods.GET,
                s3.HttpMethods.DELETE,
                s3.HttpMethods.HEAD,
            ],
            allowed_headers=["*"],
            max_age=3000,
        )




        CfnOutput(
            self, 
            "FileSystemId",
            value=file_system.file_system_id
        )
        CfnOutput(
            self,
            "AccessPointId",
            value=access_point.access_point_id
        )


