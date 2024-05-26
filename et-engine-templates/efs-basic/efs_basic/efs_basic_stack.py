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

class EfsBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vfs_id = CfnParameter(
            self,
            "vfsID"
        ).value_as_string
        security_group_id = "sg-0afc14daded6d39d0"
        vpc_id = "vpc-007a045e34604d503"

        vpc = ec2.Vpc.from_lookup(
            self,
            "ClusterVpc",
            vpc_id = vpc_id
        )
        security_group = ec2.SecurityGroup.from_security_group_id(
            self,
            "ClusterSG",
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

        
        # >>>>>
        # Lambda function with all get/upload/download/etc, mounted to the FS above.
        # https://github.com/aws-solutions/simple-file-manager-for-amazon-efs/blob/main/source/api/chalicelib/efs_lambda.py

        # Might be easier to keep EFS i/o through an intermediate lambda function (until the files get too big)
        # This architecture 
        # https://medium.com/@karantyagi1501/s3-to-efs-elastic-file-system-with-aws-lambda-8da338cbd3f3

        
        list_lambda_code = """
import os
import base64
import math
import json
import boto3
import shutil

# File manager operation events:
# list: {"operation": "list", "path": "$dir"}
# upload: {"operation": "upload", "path": "$dir", "form_data": "$form_data"}


def delete(event):
    print(event)
    path = event['path']
    name = event['name']

    file_path = path + '/' + name

    try:
        os.remove(file_path)
    except OSError:
        return {"message": "couldn't delete the file", "statusCode": 500}
    else:
        return {"message": "file deletion successful", "statusCode": 200}


def make_dir(event):
    print(event)
    path = event['path']
    name = event['name']

    new_dir = path + '/' + name

    try:
        os.mkdir(new_dir)
    except OSError:
        return {"message": "couldn't create the directory", "statusCode": 500}
    else:
        return {"message": "directory creation successful", "statusCode": 200}


def upload(event):
    print("UPLOAD REQUESTED")
    print(event)

    s3_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_key = event['Records'][0]['s3']['object']['key']

    # Set the download path in the /tmp directory
    download_path = '/tmp/' + os.path.basename(s3_key)

    # Create an S3 client
    s3_client = boto3.client('s3')

    try:
        # Download the file from S3
        s3_client.download_file(s3_bucket, s3_key, download_path)
        print(f"File downloaded: {download_path}")
    except Exception as e:
        print(f"Error downloading file: {str(e)}")

    # Move the file to the /mnt/efs directory
    destination_path = '/mnt/efs/' + os.path.basename(s3_key)
    try:
        print(download_path, destination_path)
        print(os.listdir('/tmp/'))
        print(os.listdir('/mnt/efs/'))
        shutil.move(download_path, destination_path)
        print(f"File moved to: {destination_path}")
    except Exception as e:
        print(f"Error moving file: {str(e)}")
        
    # print("After : ", os.listdir("/mnt/efs"))
    
    # Add more logic here as needed
    
    return {
        'statusCode': 200,
        'message': 'File downloaded and moved successfully',
        'body': json.dumps(event)
    }

    
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
    # get path to list
    # try:
    #     path = event['path']
    # except KeyError:
    #     return {"message": "missing required parameter: path", "statusCode": 400}

    try:
        dir_items = []
        file_items = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            dir_items.extend(dirnames)
            file_items.extend(filenames)
            break
    except Exception as error:
        print(error)
        return {"message": "unable to list files", "statusCode": 500}
    else:
        return {"path": path, "directories": dir_items, "files": file_items, "statusCode": 200}


def handler(event, _context):
    # get operation type
    try:
        if "Records" in event:
            operation_type = "upload"
            path = None
        else:
            operation_type = event['operation']
            
    except KeyError:
        return {"message": "missing required parameter: operation", "statusCode": 400}
    else:
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
        if operation_type == 'make_dir':
            make_dir_result = make_dir(event)
            return make_dir_result
        if operation_type == 'download':
            download_result = download(event)
            return download_result
        """
        list_lambda_function = _lambda.Function(
            self,
            "VFSLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "index.handler",
            code=_lambda.Code.from_inline(list_lambda_code),
            timeout = Duration.seconds(30),
            vpc=vpc,
            function_name = "vfs-" + vfs_id,
            filesystem = _lambda.FileSystem.from_efs_access_point(
                access_point,
                "/mnt/efs"
            ),
        )
        # TODO
        # - S3 buckets and trigger
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
            # s3.NotificationKeyFilter(
            #     prefix="uploads/"
            # )
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
            allowed_methods=[s3.HttpMethods.GET],
            allowed_headers=["*"],
            max_age=3000,
        )
        upload_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect = iam.Effect.ALLOW,
                actions = ['s3:GetObject'],
                resources = [f"{upload_bucket.bucket_arn}/*"],
                principals = [iam.AnyPrincipal()]
            )
        )
        # <<<<<



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


