from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

class ToolTemplate(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, network, template_bucket, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        tools_update_lambda = _lambda.Function(
            self, 'tool-template-update',
            description="Script to update computing templates",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.update.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=network.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=network.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[network.database_lambda_security_group]
        )
        database.grant_access(tools_update_lambda)
        tools_update_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:UpdateStack',
                    'ssm:GetParameters',
                    's3:*',
                    'ec2:*',
                    'iam:*',
                    'ecr:CreateRepository',
                    'ecr:DeleteRepository',
                    'ecr:DescribeRepositories',
                    'ecs:CreateCluster',
                    'ecs:DeleteCluster',
                    'ecs:DescribeClusters',
                    'ecs:RegisterTaskDefinition',
                    'ecs:DeregisterTaskDefinition',
                    'ecs:DescribeTaskDefinition',
                    'iam:PutRolePolicy',
                    'iam:GetRolePolicy',
                    'iam:DeleteRolePolicy',
                    'iam:AttachRolePolicy',
                    'iam:DetachRolePolicy',
                    'iam:CreateRole',
                    'iam:DeleteRole',
                    'iam:GetRole',
                    'iam:PassRole',
                    'logs:DeleteLogGroup',
                    'codebuild:CreateProject',
                    'codebuild:DeleteProject',
                    'codebuild:UpdateProject',
                    'lambda:CreateFunction',
                    'lambda:DeleteFunction',
                    'lambda:GetFunction',
                    'lambda:AddPermission',
                    'lambda:RemovePermission',
                    'lambda:InvokeFunction',
                    'lambda:UpdateFunctionCode',
                ],
                resources=['*']
            )
        )

        # template_bucket.add_event_notification(
        #     s3.EventType.OBJECT_CREATED, 
        #     s3n.LambdaDestination(tools_update_lambda)
        # )


class VfsTemplate(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, network, template_bucket, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        vfs_update_lambda = _lambda.Function(
            self, 'vfs-template-update',
            description="Script to update storage templates",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.update.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=network.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=network.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[network.database_lambda_security_group]
        )
        database.grant_access(vfs_update_lambda)
        vfs_update_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:*',
                    'lambda:*',
                    's3:*',
                    'efs:*',
                    'ssm:*',
                    'iam:*',
                    'ec2:*',
                    'elasticfilesystem:DeleteMountTarget'
                ],
                resources=['*']
            )
        )

        template_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, 
            s3n.LambdaDestination(vfs_update_lambda)
        )

class Templates(Stack):
    def __init__(self, scope: Construct, construct_id: str, network, database, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        template_bucket = s3.Bucket(self, "Templates", bucket_name="et-engine-templates")
        ToolTemplate(self, "ToolTemplate", database, network, template_bucket)
        VfsTemplate(self, "VfsTemplate", database, network, template_bucket)