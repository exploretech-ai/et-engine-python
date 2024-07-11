from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct


class DataTransfer(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.upload_image = ecr_assets.DockerImageAsset(self, "ContainerImage", 
            directory="docker/data_upload",
            platform=ecr_assets.Platform.LINUX_AMD64
        )   

        self.data_upload_task_role = iam.Role(
            self,
            "DataUploadRole",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
        self.data_upload_task_role.add_to_policy(
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
        
        self.launch_download_from_s3_to_efs = _lambda.Function(
            self,
            "vfs-transfer-task-launcher",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.data_upload_lambda.handler",
            code=_lambda.Code.from_asset('lambda'),
            timeout = Duration.minutes(5)
        )
        self.launch_download_from_s3_to_efs.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:DescribeStacks',
                    'ecs:RegisterTaskDefinition',
                    'iam:PassRole',
                    'ecs:RunTask',
                    # 's3:*'
                ],
                resources=[
                    "*"
                ]
            )
        )

