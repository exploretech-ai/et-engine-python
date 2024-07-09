from aws_cdk import (
    Stack,
    Size,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
)
from constructs import Construct

# https://github.com/aws-samples/aws-cdk-examples/blob/main/typescript/ecs/ecs-service-with-advanced-alb-config/index.ts
class WebServer(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, ecs_cluster, database, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        web_server_image = ecr_assets.DockerImageAsset(self, "WebServerImage", 
            directory="docker/data_download",
            platform=ecr_assets.Platform.LINUX_AMD64
        )   
        web_server_fargate_task = ecs.FargateTaskDefinition(self, "WebServerTaskDefinition")
        web_server_fargate_task.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue',
                ],
                resources=[
                    "arn:aws:secretsmanager:us-east-2:734818840861:secret:api_key_fernet_key-bjdEbo",
                    "arn:aws:secretsmanager:us-east-2:734818840861:secret:RDSSecretA2B52E34-oFnaTiUxNkh4-Wu8arW"
                ]
            )
        )
        web_server_fargate_task.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:*',
                    's3:*',
                    'ecr:*',
                    'elasticfilesystem:*',
                    'lambda:*',
                    'ec2:*',
                    'ssm:*',
                    'ecs:*',
                    'elasticloadbalancing:*',
                    'codebuild:*',
                    'logs:*',
                ],
                resources=['*']
            )
        )
        # web_server_fargate_task.add_volume(
        #     name="vfs-cafc9439-02ef-4c86-9110-6abff2c05b68",
        #     efs_volume_configuration=ecs.EfsVolumeConfiguration(
        #         file_system_id="fs-09e0c241485f4226e",
        #         authorization_config=ecs.AuthorizationConfig(
        #             access_point_id="fsap-021d0d9759a6302fd"
        #         ),
        #         transit_encryption="ENABLED"
        #     )
        # )
        web_server_container = web_server_fargate_task.add_container("WebServerContainer",
            image=ecs.ContainerImage.from_docker_image_asset(web_server_image),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="WebServerContainer",
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                max_buffer_size=Size.mebibytes(25)
            ),
            environment={
                'DATABASE_SECRET_NAME': "RDSSecretA2B52E34-oFnaTiUxNkh4",
                'DATABASE_NAME': "EngineMasterDB",
                'FERNET_KEY_SECRET_NAME': "api_key_fernet_key",
                'SECRET_REGION': "us-east-2",
            }
        )
        # web_server_container.add_mount_points(
        #     ecs.MountPoint(
        #         container_path="/mnt/cafc9439-02ef-4c86-9110-6abff2c05b68",
        #         read_only=False,
        #         source_volume="vfs-cafc9439-02ef-4c86-9110-6abff2c05b68"
        #     )
        # )
        web_server_container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                host_port=80
            )
        )

        fargate_spot_capacity_provider = ecs.CapacityProviderStrategy(
            capacity_provider="FARGATE_SPOT",
            weight=2,
            base=0
        )
        fargate_capacity_provider = ecs.CapacityProviderStrategy(
            capacity_provider="FARGATE",
            weight=1,
            base=1       
        )

        web_server_fargate_service = ecs.FargateService(self, "WebServerFargateService",
            cluster=ecs_cluster,
            task_definition=web_server_fargate_task,
            capacity_provider_strategies=[
                fargate_spot_capacity_provider,
                fargate_capacity_provider
            ],
            security_groups=[database.fargate_service_security_group]
        )

        self.load_balancer = elbv2.NetworkLoadBalancer(self, "WebServerLoadBalancer", 
            vpc=vpc,
            internet_facing=True,   
        )
        listener = self.load_balancer.add_listener("WebServerLoadBalancerListener", 
            port=80,
        )
        listener.add_targets("WebServerLoadBalancerListenerTarget", 
            port=80,
            targets=[web_server_fargate_service],
            health_check=elbv2.HealthCheck(
                enabled=True,
            )
        )
        