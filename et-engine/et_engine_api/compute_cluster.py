from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling,
    aws_logs as logs,
)
from constructs import Construct


class ComputeCluster(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "ClusterVpc2",
            vpc_name='ClusterVpc2'
        )
        self.ecs_cluster = ecs.Cluster(
            self, 
            "Cluster",
            vpc=self.vpc
        )

        auto_scaling_group = autoscaling.AutoScalingGroup(self, "ASG",
            vpc=self.vpc,
            instance_type=ec2.InstanceType("t2.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            min_capacity=0,
            max_capacity=250,
            group_metrics=[autoscaling.GroupMetrics.all()],
            key_name="hpc-admin",
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
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
        auto_scaling_group.add_user_data(
            'echo "ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=10m" >> /etc/ecs/ecs.config',
            'echo "ECS_IMAGE_PULL_BEHAVIOR=once" >> /etc/ecs/ecs.config'
        )
        auto_scaling_group.protect_new_instances_from_scale_in()
        capacity_provider = ecs.AsgCapacityProvider(self, "AsgCapacityProvider",
            auto_scaling_group=auto_scaling_group,
            capacity_provider_name="AsgCapacityProvider"
        )
        self.ecs_cluster.add_asg_capacity_provider(capacity_provider)
        self.ecs_cluster.add_default_capacity_provider_strategy([
            ecs.CapacityProviderStrategy(
                capacity_provider=capacity_provider.capacity_provider_name
            )
        ])

        
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
            log_group_name="EngineLogGroup"
        )

        security_group = ec2.SecurityGroup(
            self,
            "EFSSG",
            vpc=self.vpc,
            allow_all_outbound = True,
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(2049)
        )