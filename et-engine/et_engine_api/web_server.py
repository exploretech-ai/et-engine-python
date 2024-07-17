from aws_cdk import (
    Stack,
    Size,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_certificatemanager as ctf,
    aws_route53 as route53,
    aws_route53_targets as r53t,
)
from constructs import Construct

# https://github.com/aws-samples/aws-cdk-examples/blob/main/typescript/ecs/ecs-service-with-advanced-alb-config/index.ts
class WebServer(Stack):
    def __init__(self, scope: Construct, construct_id: str, network, compute, database, batch, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)  

        env = config['env']
        subdomain = config['subdomain']  

        zone = route53.HostedZone.from_hosted_zone_attributes(self, "zone", 
            hosted_zone_id="Z07247471MNWCOVOV0VX5",
            zone_name="exploretech.ai"
        )
        certificate = ctf.Certificate(self, "apiCert", 
            domain_name=f"{subdomain}.exploretech.ai",
            validation=ctf.CertificateValidation.from_dns(zone)
        )  
        
        web_server_image = ecr_assets.DockerImageAsset(self, "WebServerImage", 
            directory="docker/api",
            platform=ecr_assets.Platform.LINUX_AMD64
        )   
        
        self.web_server_fargate_task = ecs.FargateTaskDefinition(self, "WebServerTaskDefinition")
        self.web_server_fargate_task.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue',
                ],
                resources=[
                    "arn:aws:secretsmanager:us-east-2:734818840861:secret:api_key_fernet_key-bjdEbo",
                    database.database_secret.secret_arn
                ]
            )
        )
        self.web_server_fargate_task.add_to_task_role_policy(
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
                    'iam:*',
                    'batch:*'
                ],
                resources=['*']
            )
        )
        self.web_server_fargate_task.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    'sqs:*'
                ],
                resources=[batch.job_submitter_queue.queue_arn]
            )
        )

        self.web_server_container = self.web_server_fargate_task.add_container("WebServerContainer",
            image=ecs.ContainerImage.from_docker_image_asset(web_server_image),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="WebServerContainer",
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                max_buffer_size=Size.mebibytes(25)
            ),
            environment={
                'DATABASE_SECRET_NAME': database.database_secret.secret_name,
                'DATABASE_NAME': database.database_name,
                'FERNET_KEY_SECRET_NAME': "api_key_fernet_key",
                'SECRET_REGION': "us-east-2",
                'JOB_SUBMISSION_QUEUE_URL': batch.job_submitter_queue.queue_url
            }
        )
        self.web_server_container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                host_port=80
            )
        )

        

        # NOTE: This is hard-coded as an import because using `network.fargate_service_security_group` causes a cyclical reference error
        fargate_service_security_group = ec2.SecurityGroup.from_security_group_id(self, "ImportedFargateServiceSecurityGroup",
            security_group_id="sg-0e3f3ed33ff60aab4"
        )
        web_server_fargate_service = ecs.FargateService(self, "WebServerFargateService",
            cluster=compute.ecs_cluster,
            task_definition=self.web_server_fargate_task,
            capacity_provider_strategies=[
                compute.fargate_spot_capacity_provider,
                compute.fargate_capacity_provider
            ],
            security_groups=[fargate_service_security_group]
        )
        load_balancer_target = web_server_fargate_service.load_balancer_target(
            container_name=self.web_server_container.container_name,
            container_port=80
        )

        self.load_balancer = elbv2.ApplicationLoadBalancer(self, "WebServerLoadBalancer",
            vpc=network.vpc,
            internet_facing=True
        )        
        listener = self.load_balancer.add_listener("WebServerLoadBalancerListener",
            port=443,
            certificates=[certificate]                                          
        )
        listener.add_targets("WebServerLoadBalancerListenerTarget",
            port=80,
            targets=[load_balancer_target],
            health_check=elbv2.HealthCheck(
                enabled=True,
            )
        )

        route53.ARecord(self, "apiDNS",
            zone=zone,
            record_name=subdomain,
            target=route53.RecordTarget.from_alias(r53t.LoadBalancerTarget(self.load_balancer))
        )

        # NOTE: This will have to be automatically updated
        file_system_mount_params = [
            ["cafc9439-02ef-4c86-9110-6abff2c05b68", "fs-09e0c241485f4226e", "fsap-021d0d9759a6302fd"],
            ["f35dc82f-0019-43ef-ae9c-51ad9607c0bd", "fs-096e4d7658a8c4732", "fsap-02c968693bb54f224"],
            ["24474f05-3256-48af-a68f-ddf7fb29cc89", "fs-06b2a6202057d1fbb", "fsap-0ab36f111fed24679"],
            ["427e2294-1365-4b95-9237-a0314463c5bd", "fs-0b2b40344bb282514", "fsap-058764ea78df568ed"],
            ["dde97cc8-d4e2-4a8c-946a-5f5226346b9a", "fs-0418f73e0e9a18931", "fsap-08306384f08e7f341"],
            ["b0e39682-01bc-4141-8a1d-cc9b8cfc74ea", "fs-098ca96ed0dc2295b", "fsap-0b456caa8e25db8bf"],
            ["a3927777-c26b-484d-a74a-89eb163f88cc", "fs-0808d3e89eff8a345", "fsap-045f50913c11a1193"]
        ]
        for p in file_system_mount_params:
            self.mount_volume(p[0], p[1], p[2])

            

    def mount_volume(self, vfs_id, file_system_id, access_point_id):
        self.web_server_fargate_task.add_volume(
            name="vfs-" + vfs_id,
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=file_system_id,
                authorization_config=ecs.AuthorizationConfig(
                    access_point_id=access_point_id
                ),
                transit_encryption="ENABLED"
            )
        )  
        self.web_server_container.add_mount_points(
            ecs.MountPoint(
                container_path="/mnt/" + vfs_id,
                read_only=False,
                source_volume="vfs-" + vfs_id
            )
        )
