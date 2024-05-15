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

        # Upload data
        # -----------
        # User - Request -> API
        # API - Presigned POST -> User
        # User - Presigned POST w/ Data -> S3 
        # Event triggers lambda
        # Lambda - New Data -> EFS
        # RESOURCES: s3 bucket, lambda (mounted to this FS), s3 event trigger connected to lambda
        # -----------
        #
        # Download data
        # -------------
        # User makes a data request, selecting files
        # User - Desired Files -> API
        # API -> Lambda Handler  
        # Lambda Handler -> VFS-specific lambda async
        # VFS-Specific lambda - Requested Data ZIP -> S3 Download bucket
        # User -> Download queue (lists available downloads)
        # User - Download this zip -> API (GET /vfs/{vfsID}/downloads/{downloadID})
        # API - Presigned URL -> User
        # User - Presigned URL -> Data download
        # RESOURCES: s3 bucket, lambda mounted to this FS
        # -------------
        #
        # List directory
        # --------------
        # User - List Request -> API
        # API -> Lambda, looks up other lambda needed
        # Lambda -> Invoke FS-lambda to list
        # Collect response and forward back to user
        # RESOURCES: lambda mounted to this VFS
        # --------------
        #
        # Delete item
        # -----------
        # User - Delete Request -> API
        # API -> Lambda, looks up other lambda
        # Lambda -> Invoke FS-lambda to delete
        # FS-lambda deletes and returns response
        # RESOURCES: lambda mounted to this VFS
        # -----------
        # 
        # TOTAL RESOURCES
        # ---------------
        # Upload s3 bucket with delete lifecycle
        # Download s3 bucket
        # Lambda that handles: list, upload, download, delete
        # S3 trigger connected to Lambda
        #
        # DEVELOPMENT PLAN:
        #     1. Provision Lambda, get List command working, even if there's no data yet
        #     2. Provision Upload S3 bucket, get it to connect with EFS by running a TEST file
        #     3. Get download workflow started, to two-step "shopping cart"-like workflow
        #     4. Implement "shopping cart" downloads
        #     5. Finish off with the delete endpoint, which should be easy by this point

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

    # # Additional logic
    # with open(download_path, 'r') as file:
    #     file_content = file.read()
    #     print(f"File content: {file_content}")

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

    # "{'operation': 'upload', 'path': '/mnt/efs', 'chunk_data': {'dzuuid': '10f726ea-ae1d-4363-9a97-4bf6772cd4df', 'dzchunkindex': '0', 'dzchunksize': '1000000', 'dztotalchunkcount': '1', 'dzchunkbyteoffset': '0', 'filename': 'Log at 2020-08-11 12-17-21 PM.txt', 'content': '(Emitted value instead of an instance of Error)'}}"
    # path = event['path']
    # filename = event['chunk_data']['filename']
    # file_content_decoded = base64.b64decode(event['chunk_data']['content'])
    # current_chunk = int(event['chunk_data']['dzchunkindex'])
    # save_path = os.path.join(path, filename)

    # if os.path.exists(save_path) and current_chunk == 0:
    #     return {"message": "File already exists", "statusCode": 400}

    # try:
    #     with open(save_path, 'ab') as f:
    #         f.seek(int(event['chunk_data']['dzchunkbyteoffset']))
    #         f.write(file_content_decoded)
    # except OSError as error:
    #     print('Could not write to file: {error}'.format(error=error))
    #     return {"message": "couldn't write the file to disk", "statusCode": 500}

    # total_chunks = int(event['chunk_data']['dztotalchunkcount'])

    # if current_chunk + 1 == total_chunks:
    #     if int(os.path.getsize(save_path)) != int(event['chunk_data']['dztotalfilesize']):
    #         print("File {filename} was completed, but there is a size mismatch. Was {size} but expected {total}".format(filename=filename, size=os.path.getsize(save_path), total=event['chunk_data']['dztotalfilesize']))
    #         return {"message": "Size mismatch", "statusCode": 500}
    #     else:
    #         print("file {filename} has been uploaded successfully".format(filename=filename))
    #         return {"message": "File uploaded successfuly", "statusCode": 200}
    # else:
    #     print("Chunk {current_chunk} of {total_chunks} for file {filename} complete".format(current_chunk=current_chunk + 1 , total_chunks=total_chunks, filename=filename))
    #     return {"message": "Chunk upload successful", "statusCode": 200}


def download(event):
    # first call {"path": "./", "filename": "test.txt"}
    # successive calls
    # {"path": "./", "filename": "test_video.mp4", "chunk_data": {'dzchunkindex': chunk['dzchunkindex'],
    # 'dzchunkbyteoffset': chunk['dzchunkbyteoffset']}}
    path = event['path']
    filename = event['filename']
    file_path = os.path.join(path, filename)
    chunk_size = 2000000  # bytes
    file_size = os.path.getsize(file_path)
    chunks = math.ceil(file_size / chunk_size)

    if "chunk_data" in event:
        start_index = event['chunk_data']['dzchunkbyteoffset']
        current_chunk = event['chunk_data']['dzchunkindex']
        try:
            with open(file_path, 'rb') as f:
                f.seek(start_index)
                file_content = f.read(chunk_size)
                encoded_chunk_content = str(base64.b64encode(file_content), 'utf-8')
                chunk_offset = start_index + chunk_size
                chunk_number = current_chunk + 1

                return {"dzchunkindex": chunk_number, "dztotalchunkcount": chunks, "dzchunkbyteoffset": chunk_offset,
                        "chunk_data": encoded_chunk_content, "dztotalfilesize": file_size}
        except OSError as error:
            print('Could not read file: {error}'.format(error=error))
            return {"message": "couldn't read the file from disk", "statusCode": 500}

    else:
        start_index = 0
        try:
            with open(file_path, 'rb') as f:
                f.seek(start_index)
                file_content = f.read(chunk_size)
                encoded_chunk_content = str(base64.b64encode(file_content), 'utf-8')
                chunk_number = 0
                chunk_offset = chunk_size

                return {"dzchunkindex": chunk_number, "dztotalchunkcount": chunks, "dzchunkbyteoffset": chunk_offset,
                        "chunk_data": encoded_chunk_content, "dztotalfilesize": file_size}

        except OSError as error:
            print('Could not read file: {error}'.format(error=error))
            return {"message": "couldn't read the file from disk", "statusCode": 500}


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
            path = event['path']
    except KeyError:
        return {"message": "missing required parameter: operation", "statusCode": 400}
    else:
        if operation_type == 'upload':
            upload_result = upload(event)
            return upload_result
        if operation_type == 'list':
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

        # file_system = efs.FileSystem(
        #     self,
        #     "MyEfsFileSystem",
        #     vpc = vpc
        # )
        

        # instance = ec2.Instance(
        #     scope=self,
        #     id="ec2Instance",
        #     instance_name="my_ec2_instance",
        #     instance_type=ec2.InstanceType.of(
        #         instance_class=ec2.InstanceClass.BURSTABLE2,
        #         instance_size=ec2.InstanceSize.MICRO,
        #     ),
        #     machine_image=ec2.AmazonLinuxImage(
        #         generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
        #     ),
        #     vpc=vpc,
        #     key_pair=ec2.KeyPair.from_key_pair_name(self, "my-key", "hpc-admin"),
        #     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        # )

        # file_system.connections.allow_default_port_from(instance)
        # instance.connections.allow_from_any_ipv4(ec2.Port.tcp(22))
        # file_system.add_to_resource_policy(
        #     iam.PolicyStatement(
        #         actions = ["elasticfilesystem:ClientMount"],
        #         # resources=[file_system.file_system_arn],
        #         effect=iam.Effect.ALLOW,
        #         principals=[iam.AnyPrincipal()]
        #     )
        # )

        # # Does the mounting
        # instance.user_data.add_commands(
        #     "echo 'STARTING USER COMMANDS'"
        #     "yum check-update -y",
        #     "yum upgrade -y",
        #     "yum install -y amazon-efs-utils",
        #     "yum install -y nfs-utils",
        #     "file_system_id_1=" + file_system.file_system_id + ".efs." + self.region + ".amazonaws.com", # <-- THIS NEEDS TO BE THE EFS DNS
        #     "echo ${file_system_id_1}",
        #     "efs_mount_point_1=/mnt/efs/fs1",
        #     "echo 'MAKING DIRECTORY'",
        #     'mkdir -p "${efs_mount_point_1}"',
        #     "echo 'MOUNTING'",
        #     'sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 ${file_system_id_1}:/ ${efs_mount_point_1}',
        #     "echo 'SUCCESS!'",
        #     # See here for commands to install docker on command https://medium.com/appgambit/part-1-running-docker-on-aws-ec2-cbcf0ec7c3f8
        # )

        # CfnOutput(self, "Instance DNS", value=instance.instance_public_dns_name)
        # CfnOutput(self, "EFS DNS", value=file_system.file_system_id + ".efs." + self.region + ".amazonaws.com")


        #



# class EfsBasicStack(Stack):

#     def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
#         super().__init__(scope, construct_id, **kwargs)


#         # ============ These will go in the bigger API ============
#         vpc = ec2.Vpc(
#             self,
#             "DevVPC"
#         )

#         cluster = ecs.Cluster(
#             self, 
#             "Cluster",
#             vpc=vpc
#         )

#         cluster.add_capacity("DefaultAutoScalingGroupCapacity",
#             instance_type=ec2.InstanceType("t2.micro"),
#             desired_capacity=3
#         )

        # TODO
        # ecs task execution role
        # codebuild role

        # ==========================================================


        # =============== These will stay tool-specific =========
        # task definition (need cluster name)
        # code bucket
        # codebuild project
        # log group
        # ECR repository
        # codebuild trigger

        # ===============



        # autoscaling.AutoScalingGroup(self, "ASG",
        #     vpc=vpc,
        #     instance_type=instance_type, # ec2.InstanceType
        #     machine_image=machine_image, # ec2.IMachineImage

        #     # ...

        #     init=ec2.CloudFormationInit.from_elements(
        #         ec2.InitFile.from_string("/etc/my_instance", "This got written during instance startup")),
        #     signals=autoscaling.Signals.wait_for_all(
        #         timeout=Duration.minutes(10)
        #     )
        # )

        # """
        # Now, when I run tool/execute on this hardware the lambda will use boto3 to launch an ECS task definition on the ECS cluster for that instance type
        # https://stackoverflow.com/questions/49991256/how-to-run-docker-image-in-kubernetes-pod
        # """

        # vpc = ec2.Vpc(self, "Vpc", max_azs=1)
        # cluster = ecs.Cluster(self, "EcsCluster", vpc=vpc)
        # cluster.add_asg_capacity_provider(provider, *, can_containers_access_instance_role=None, machine_image_type=None, spot_instance_draining=None, topic_encryption_key=None)
        # task_definition = ecs.TaskDefinition(self, "TaskDef",
        #     memory_limit_mi_b=512,
        #     cpu=256,
        #     compatibility=ecs.Compatibility.EC2
        # )
        # task_definition.add_container("WebContainer",
        #     image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample")
        # )



        #


