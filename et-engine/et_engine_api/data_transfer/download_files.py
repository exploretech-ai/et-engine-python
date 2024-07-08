from aws_cdk import (
    Stack,
    Size,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct

# https://github.com/aws-samples/aws-cdk-examples/blob/main/typescript/ecs/ecs-service-with-advanced-alb-config/index.ts
class DownloadFiles(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, ecs_cluster, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        self.download_image = ecr_assets.DockerImageAsset(self, "DownloadImage", 
            directory="docker/data_download",
            platform=ecr_assets.Platform.LINUX_AMD64
        )   
        download_task_fargate = ecs.FargateTaskDefinition(self, "DownloadTaskDefinition")
        download_task_fargate.add_volume(
            name="vfs-cafc9439-02ef-4c86-9110-6abff2c05b68",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id="fs-09e0c241485f4226e",
                authorization_config=ecs.AuthorizationConfig(
                    access_point_id="fsap-021d0d9759a6302fd"
                ),
                transit_encryption="ENABLED"
            )
        )
        download_container = download_task_fargate.add_container("DownloadContainer",
            image=ecs.ContainerImage.from_docker_image_asset(self.download_image),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="DownloadContainer",
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                max_buffer_size=Size.mebibytes(25)
            )
        )
        download_container.add_mount_points(
            ecs.MountPoint(
                container_path="/mnt/cafc9439-02ef-4c86-9110-6abff2c05b68",
                read_only=False,
                source_volume="vfs-cafc9439-02ef-4c86-9110-6abff2c05b68"
            )
        )
        download_container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                host_port=80
            )
        )
        security_group = ec2.SecurityGroup(self, "LoadBalancerSecurityGroup", vpc=vpc)
        security_group.add_ingress_rule(
            connection=ec2.Port.tcp(80),
            peer=ec2.Peer.any_ipv4()
        )
        download_service = ecs.FargateService(self, "DownloadService",
            cluster=ecs_cluster,
            task_definition=download_task_fargate ,
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE_SPOT",
                    weight=2,
                    base=0
                ), 
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE",
                    weight=1,
                    base=1       
                )
            ],
            security_groups=[security_group]
        )
        self.load_balancer = elbv2.NetworkLoadBalancer(self, "LoadBalancer", 
            vpc=vpc,
            internet_facing=False,   
        )
        listener = self.load_balancer.add_listener("Listener", 
            port=80,
        )
        listener.add_targets("target", 
            port=80,
            targets=[download_service],
            health_check=elbv2.HealthCheck(
                enabled=True,
            )
        )
        
        self.vpc_link = apigateway.VpcLink(self, "link",
            targets=[self.load_balancer]
        )