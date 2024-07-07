from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct


class DataTransfer(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.upload_image = ecr_assets.DockerImageAsset(self, "ContainerImage", 
            directory="docker/data_upload",
            platform=ecr_assets.Platform.LINUX_AMD64
        )   

        self.data_upload_task_role = iam.Role(
            self,
            "DataUploadRole",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
        self.data_upload_task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'ecr:*',
                    'elasticfilesystem:*',
                    "sts:*",
                    "logs:*",
                    "s3:*"
                ],
                resources=['*']
            )
        )
        
        self.launch_download_from_s3_to_efs = _lambda.Function(
            self,
            "vfs-transfer-task-launcher",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.data_upload_lambda.handler",
            code=_lambda.Code.from_asset('lambda'),
            timeout = Duration.minutes(5)
        )
        self.launch_download_from_s3_to_efs.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:DescribeStacks',
                    'ecs:RegisterTaskDefinition',
                    'iam:PassRole',
                    'ecs:RunTask',
                    # 's3:*'
                ],
                resources=[
                    "*"
                ]
            )
        )

        
        # https://github.com/aws-samples/aws-cdk-examples/blob/main/typescript/ecs/ecs-service-with-advanced-alb-config/index.ts
        # self.download_image = ecr_assets.DockerImageAsset(self, "DownloadImage", 
        #     directory="docker/data_download",
        #     platform=ecr_assets.Platform.LINUX_AMD64
        # )   
        # download_task_fargate = ecs.FargateTaskDefinition(self, "DownloadTaskDefinition")
        # download_task_fargate.add_volume(
        #     name="EfsVolume",
        #     efs_volume_configuration=ecs.EfsVolumeConfiguration(
        #         file_system_id="fs-09e0c241485f4226e",
        #         authorization_config=ecs.AuthorizationConfig(
        #             access_point_id="fsap-021d0d9759a6302fd"
        #         ),
        #         transit_encryption="ENABLED"
        #     )
        # )
        # download_container = download_task_fargate.add_container("DownloadContainer",
        #     image=ecs.ContainerImage.from_docker_image_asset(self.download_image)
        # )
        # download_container.add_port_mappings(
        #     ecs.PortMapping(
        #         container_port=80,
        #         host_port=80
        #     )
        # )
        # security_group = ec2.SecurityGroup(self, "LoadBalancerSecurityGroup", vpc=cluster.vpc)
        # security_group.add_ingress_rule(
        #     connection=ec2.Port.tcp(80),
        #     peer=ec2.Peer.any_ipv4()
        # )
        # download_service = ecs.FargateService(self, "DownloadService",
        #     cluster=cluster.ecs_cluster,
        #     task_definition=download_task_fargate ,
        #     capacity_provider_strategies=[
        #         ecs.CapacityProviderStrategy(
        #             capacity_provider="FARGATE_SPOT",
        #             weight=2,
        #             base=0
        #         ), 
        #         ecs.CapacityProviderStrategy(
        #             capacity_provider="FARGATE",
        #             weight=1,
        #             base=1       
        #         )
        #     ],
        #     security_groups=[security_group]
        # )
        # load_balancer = elbv2.NetworkLoadBalancer(self, "LoadBalancer", 
        #     vpc=cluster.vpc,
        #     internet_facing=False,   
        # )
        # listener = load_balancer.add_listener("Listener", 
        #     port=80,
        # )
        # listener.add_targets("target", 
        #     port=80,
        #     targets=[download_service],
        #     health_check=elbv2.HealthCheck(
        #         enabled=True,
        #     )
        # )
        

        # vpc_link = apigateway.VpcLink(self, "link",
        #     targets=[load_balancer]
        # )
        # download_resource = api.api.root.add_resource("tmp")
        # integration = apigateway.Integration(
        #     type=apigateway.IntegrationType.HTTP_PROXY,
        #     uri="http://" + load_balancer.load_balancer_dns_name,
        #     integration_http_method="ANY",
        #     options=apigateway.IntegrationOptions(
        #         connection_type=apigateway.ConnectionType.VPC_LINK,
        #         vpc_link=vpc_link
        #     )
        # )

        # download_resource.add_method(
        #     "GET",
        #     integration=integration,
        #     method_responses=[{
        #         'statusCode': '200',
        #         'responseParameters': {
        #             'method.response.header.Content-Type': True,
        #         },
        #         'responseModels': {
        #             'application/json': apigateway.Model.EMPTY_MODEL,
        #         },
        #     }],
        #     authorizer = api.key_authorizer,
        #     authorization_type = apigateway.AuthorizationType.CUSTOM,
        # )

