from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling,
    aws_logs as logs,
)
from constructs import Construct

from .data_transfer.download_files import DownloadFiles
from .data_transfer.upload_files import UploadFiles

class ComputeCluster(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env = config['env']

        # self.vpc = ec2.Vpc(
        #     self,
        #     "ClusterVpc",
        #     vpc_name='ClusterVpc'
        # )
        self.vpc = database.vpc
        self.ecs_cluster = ecs.Cluster(
            self, 
            "Cluster",
            vpc=self.vpc
        )

        self.auto_scaling_group = autoscaling.AutoScalingGroup(self, "ASG",
            vpc=self.vpc,
            instance_type=ec2.InstanceType("t2.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            min_capacity=0,
            max_capacity=250,
            group_metrics=[autoscaling.GroupMetrics.all()],
            # key_name="hpc-admin",
            # vpc_subnets=ec2.SubnetSelection(
            #     subnet_type=ec2.SubnetType.PUBLIC
            # ),
            block_devices=[
                autoscaling.BlockDevice(
                    device_name="/dev/xvdcz",
                    volume=autoscaling.BlockDeviceVolume.ebs(64)
                ),
                autoscaling.BlockDevice(
                    device_name="/dev/xvda",
                    volume=autoscaling.BlockDeviceVolume.ebs(64)
                )
            ]
            # key_pair=ec2.KeyPair.from_key_pair_name(self, "my-key", "hpc-admin")
        )
        self.auto_scaling_group.add_user_data(
            'echo "ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=10m" >> /etc/ecs/ecs.config',
            'echo "ECS_IMAGE_PULL_BEHAVIOR=once" >> /etc/ecs/ecs.config'
        )
        self.auto_scaling_group.protect_new_instances_from_scale_in()
        self.capacity_provider = ecs.AsgCapacityProvider(self, "AsgCapacityProvider",
            auto_scaling_group=self.auto_scaling_group,
            capacity_provider_name="CpuCapacityProvider"
        )
        self.ecs_cluster.add_asg_capacity_provider(self.capacity_provider)
        self.ecs_cluster.add_default_capacity_provider_strategy([
            ecs.CapacityProviderStrategy(
                capacity_provider=self.capacity_provider.capacity_provider_name
            )
        ])

        self.ecs_cluster.enable_fargate_capacity_providers()
        
        self.task_role = iam.Role(
            self,
            "ECSTaskRole",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
        self.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'ecr:*',
                    'elasticfilesystem:*',
                    "sts:*",
                    "logs:*"
                ],
                resources=['*']
            )
        )
        logs.LogGroup(
            self,
            "LogGroup",
            # log_group_name="EngineLogGroup"
        )

        self.security_group = ec2.SecurityGroup(
            self,
            "EFSSG",
            vpc=self.vpc,
            allow_all_outbound = True,
        )
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(2049)
        )

        self.upload_files = UploadFiles(self, "UploadFilesInfra")
        self.download_files = DownloadFiles(self, f"DownloadFilesInfra{env}", self.vpc, self.ecs_cluster, database)
