from aws_cdk import (
    Stack,
    CfnOutput,
    PhysicalName,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_s3_notifications as s3n,
    aws_ecs as ecs,
    aws_ecr_assets as ecr_assets
)
from constructs import Construct


class DataTransfer(Stack):
    def __init__(self, scope: Construct, construct_id: str, api, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        security_group_id = "sg-08ad2fb3a42e5ce01"
        vpc_id = "vpc-05c602ef885d449bc"

        vpc = ec2.Vpc.from_lookup(
            self,
            "ClusterVpc",
            vpc_id = vpc_id,
        )
        security_group = ec2.SecurityGroup.from_security_group_id(
            self,
            "ClusterSG2",
            security_group_id = security_group_id
        )

        vfs_id = "fs-0b2b40344bb282514"
        access_point_id = "fsap-058764ea78df568ed"
        
        fs = efs.FileSystem.from_file_system_attributes(self, "EFS", 
            file_system_id=vfs_id,
            security_group=security_group
        )
        access_point=efs.AccessPoint.from_access_point_attributes(self, "ap",
            access_point_id=access_point_id,
            file_system=fs
        )

        image_asset = ecr_assets.DockerImageAsset(self, "ContainerImage", 
            directory="docker/data_upload",
            platform=ecr_assets.Platform.LINUX_AMD64
        )  
        upload_container_image = ecs.ContainerImage.from_docker_image_asset(image_asset)
        CfnOutput(self, "UploadContainerUri", value=image_asset.image_uri)
        # upload_task = ecs.Ec2TaskDefinition(
        #     self,
        #     "DataUploadTask",
        #     family="data-upload",
        #     volumes=volumes
        # )
        # upload_task.add_container(
        #     "DataUploadContainer",
        #     image=upload_container_image,
        #     logging=ecs.LogDrivers.aws_logs(
        #         stream_prefix=f"data-upload",
        #         mode=ecs.AwsLogDriverMode.NON_BLOCKING,
        #     ),
        #     container_name=f"DataUpload",
        #     memory_limit_mib=14000,
        #     cpu=4096
        # )
        # upload_task.add_to_execution_role_policy(
        #     iam.PolicyStatement(
        #         actions=[
        #             'ecr:*',
        #         ],
        #         resources=['*']
        #     )
        # )       
        # upload_task.add_to_task_role_policy(
        #     iam.PolicyStatement(
        #         actions=[
        #             's3:*'
        #         ],
        #         resources=['*']
        #     )
        # )
 

        # Temporary s3 bucket
        transfer_bucket = s3.Bucket(
            self,
            "TransferBucket",
            auto_delete_objects = True,
            removal_policy=RemovalPolicy.DESTROY,
            bucket_name = "temp-data-transfer-bucket-test"
        )
        transfer_bucket.add_cors_rule(
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

        data_upload_task_role = iam.Role(
            self,
            "DataUploadRole",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
        data_upload_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'ecr:*',
                    'elasticfilesystem:*',
                    "sts:*",
                    "logs:*",
                    "s3:*"
                ],
                resources=['*']
            )
        )
        CfnOutput(self, "UploadRoleArn", value=data_upload_task_role.role_arn)

        data_upload_lambda = _lambda.Function(
            self,
            "tmp-vfs-transfer-task-launcher",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.data_upload_lambda.handler",
            code=_lambda.Code.from_asset('lambda'),
            timeout = Duration.minutes(5)
        )
        data_upload_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*'
                ],
                resources=[
                    transfer_bucket.bucket_arn,
                    transfer_bucket.bucket_arn + "/*"
                ]
            )
        )
        data_upload_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:DescribeStacks',
                    'ecs:RegisterTaskDefinition',
                    'iam:PassRole',
                    'ecs:RunTask',
                ],
                resources=[
                    "*"
                ]
            )
        )
        transfer_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, 
            s3n.LambdaDestination(data_upload_lambda),
        )

        # Temporary API resource with POST/GET
        tmp_resource = api.api.root.add_resource("tmp")
        vfs_upload_lambda = _lambda.Function(self, 'vfs-upload-transfer-launch',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.temp_upload.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.minutes(5),
            function_name=PhysicalName.GENERATE_IF_NEEDED
        )
        vfs_upload_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*'
                ],
                resources=[
                    transfer_bucket.bucket_arn,
                    transfer_bucket.bucket_arn + "/*"
                ]
            )
        )
        
        tmp_resource.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_upload_lambda),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Content-Type': True,
                },
                'responseModels': {
                    'application/json': apigateway.Model.EMPTY_MODEL,
                },
            }],
            authorizer = api.key_authorizer,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
        )



        # vfs_download_lambda = _lambda.Function(
        #     self, 'vfs-download-tmp',
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler= "vfs.temp_download.handler",
        #     code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
        #     timeout = Duration.seconds(30)
        # )
        # tmp_resource.add_method(
        #     "GET",
        #     integration=apigateway.LambdaIntegration(vfs_download_lambda),
        #     method_responses=[{
        #         'statusCode': '200',
        #         'responseParameters': {
        #             'method.response.header.Content-Type': True,
        #         },
        #         'responseModels': {
        #             'application/json': apigateway.Model.EMPTY_MODEL,
        #         },
        #     }],
        #     authorizer = api.key_authorizer,
        #     authorization_type = apigateway.AuthorizationType.CUSTOM,
        # )
        # vfs_download_lambda.add_to_role_policy(
        #     iam.PolicyStatement(
        #         actions=[
        #             's3:*'
        #         ],
        #         resources=[
        #             transfer_bucket.bucket_arn,
        #             transfer_bucket.bucket_arn + "/*"
        #         ]
        #     )
        # )

        # CfnOutput(self, "TransferBucketName", value=transfer_bucket.bucket_name)
        