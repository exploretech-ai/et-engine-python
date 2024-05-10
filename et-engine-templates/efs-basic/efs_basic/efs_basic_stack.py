from aws_cdk import (
    Stack,
    CfnOutput,
    aws_efs as efs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_autoscaling as autoscaling,
    aws_ecs as ecs,
)
from constructs import Construct

class EfsBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = None # FROM LOOKUP

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
            "echo 'SUCCESS!'",
            # See here for commands to install docker on command https://medium.com/appgambit/part-1-running-docker-on-aws-ec2-cbcf0ec7c3f8
        )

        CfnOutput(self, "Instance DNS", value=instance.instance_public_dns_name)
        CfnOutput(self, "EFS DNS", value=file_system.file_system_id + ".efs." + self.region + ".amazonaws.com")


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


