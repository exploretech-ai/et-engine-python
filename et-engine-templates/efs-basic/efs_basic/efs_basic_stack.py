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
        security_group_id = CfnParameter(
            self,
            "sgID"
        ).value_as_string
        vpc_id = CfnParameter(
            self,
            "vpcID"
        ).value_as_string
        launch_download_from_s3_to_efs_arn = CfnParameter(
            self,
            "launchDownloadFromS3ToEfsArn"
        ).value_as_string

        vpc_id = "vpc-0412712c63ab21820"

        launch_download_from_s3_to_efs = _lambda.Function.from_function_arn(self, "S3toEfs", launch_download_from_s3_to_efs_arn)

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
            s3n.LambdaDestination(launch_download_from_s3_to_efs),
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
            exposed_headers=["ETag"],
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


