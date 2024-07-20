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


class Templates(Stack):
    def __init__(self, scope: Construct, construct_id: str, network, database, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        template_bucket = s3.Bucket(self, "Templates", bucket_name="et-engine-templates")
        template_update_lambda = _lambda.Function(
            self, 'template-update',
            description="Script to update storage templates",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "update_templates.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=network.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=network.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[network.database_lambda_security_group],
            environment={
                "DATABASE_SHORT_NAME": database.database_name,
                "SECRET_NAME": database.database_secret.secret_name
            },
        )
        database.grant_access(template_update_lambda)
        template_update_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:*',
                    'codebuild:*',
                    'ec2:*',
                    'ecr:*',
                    'ecs:*',
                    'efs:*',
                    'elasticfilesystem:*',
                    'iam:*',
                    'lambda:*',
                    'logs:DeleteLogGroup',
                    's3:*',
                    'ssm:*',
                ],
                resources=['*']
            )
        )

        template_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, 
            s3n.LambdaDestination(template_update_lambda)
        )
