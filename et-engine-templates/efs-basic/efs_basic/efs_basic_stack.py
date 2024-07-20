from aws_cdk import (
    Stack,
    CfnOutput,
    CfnParameter,
    Duration,
    RemovalPolicy,
    aws_efs as efs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
)
from constructs import Construct


class EfsBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vfs_id = CfnParameter(self, "vfsID").value_as_string
        security_group_id = CfnParameter(self, "sgID").value_as_string
        file_system_id = CfnParameter(self, "fileSystemId").value_as_string
   
        security_group = ec2.SecurityGroup.from_security_group_id(self, "ClusterSG2",
            security_group_id=security_group_id
        )
        file_system = efs.FileSystem.from_file_system_attributes(self, "MasterFileSystem",
            security_group=security_group,
            file_system_id=file_system_id                           
        )

        access_point = efs.AccessPoint(self, "VfsAccessPoint",
            file_system=file_system,
            path=f"/{vfs_id}",   
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

        CfnOutput(self, "AccessPointId",
            value=access_point.access_point_id
        )


