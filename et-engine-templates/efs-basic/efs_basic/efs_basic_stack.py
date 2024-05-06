from aws_cdk import (
    Stack,
    CfnOutput,
    aws_efs as efs,
    aws_ec2 as ec2,
    aws_iam as iam
)
from constructs import Construct

class EfsBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self,
            "DevVPC"
        )

        file_system = efs.FileSystem(
            self,
            "MyEfsFileSystem",
            vpc = vpc
        )
        

        instance = ec2.Instance(
            scope=self,
            id="ec2Instance",
            instance_name="my_ec2_instance",
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.BURSTABLE2,
                instance_size=ec2.InstanceSize.MICRO,
            ),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            vpc=vpc,
            key_pair=ec2.KeyPair.from_key_pair_name(self, "my-key", "hpc-admin"),
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

        file_system.connections.allow_default_port_from(instance)
        instance.connections.allow_from_any_ipv4(ec2.Port.tcp(22))
        file_system.add_to_resource_policy(
            iam.PolicyStatement(
                actions = ["elasticfilesystem:ClientMount"],
                # resources=[file_system.file_system_arn],
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()]
            )
        )

        # Does the mounting
        instance.user_data.add_commands(
            "echo 'STARTING USER COMMANDS'"
            "yum check-update -y",
            "yum upgrade -y",
            "yum install -y amazon-efs-utils",
            "yum install -y nfs-utils",
            "file_system_id_1=" + file_system.file_system_id + ".efs." + self.region + ".amazonaws.com", # <-- THIS NEEDS TO BE THE EFS DNS
            "echo ${file_system_id_1}",
            "efs_mount_point_1=/mnt/efs/fs1",
            "echo 'MAKING DIRECTORY'",
            'mkdir -p "${efs_mount_point_1}"',
            "echo 'MOUNTING'",
            'sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 ${file_system_id_1}:/ ${efs_mount_point_1}',
            "echo 'SUCCESS!'"
        )

        CfnOutput(self, "Instance DNS", value=instance.instance_public_dns_name)
        CfnOutput(self, "EFS DNS", value=file_system.file_system_id + ".efs." + self.region + ".amazonaws.com")





