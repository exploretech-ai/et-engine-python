from aws_cdk import (
    Stack,
    aws_efs as efs,
    aws_iam as iam
)
from constructs import Construct

class FileSystems(Stack):
    def __init__(self, scope: Construct, construct_id: str, network, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)  

        self.master_file_system = efs.FileSystem(self, "MasterFileSystem",
            vpc = network.vpc,
            security_group=network.efs_security_group,
            file_system_name = "Master-File-System",
            encrypted=True
        )
        self.master_file_system.add_to_resource_policy(
            iam.PolicyStatement(
                actions = ["elasticfilesystem:*"],
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()]
            )
        )

        self.master_access_point = self.master_file_system.add_access_point(
            "WebServerAccessPoint",
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

