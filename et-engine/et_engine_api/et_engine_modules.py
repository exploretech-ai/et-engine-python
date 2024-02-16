from aws_cdk import (
    Stack,
    CfnOutput,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_logs as logs,
    aws_codebuild as codebuild
)
from constructs import Construct


class ComputeModule(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ecr_repo_name = "engine-algo-0000"
        vpc = ec2.CfnVPC(
            self,
            "ClusterVPC",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            cidr_block="10.0.0.0/16"
        )
        public_subnet = ec2.CfnSubnet(
            self,
            "PublicSubnet",
            vpc_id=vpc.attr_vpc_id,
            availability_zone="us-east-2a",
            cidr_block="10.0.0.0/18",
            map_public_ip_on_launch=True
        )
        internet_gateway = ec2.CfnInternetGateway(
            self, 
            "InternetGateway"
        )
        gateway_attachment = ec2.CfnVPCGatewayAttachment(
            self,
            "GatewayAttachment",
            vpc_id=vpc.attr_vpc_id,
            internet_gateway_id=internet_gateway.attr_internet_gateway_id
        )
        public_route_table = ec2.CfnRouteTable(
            self,
            "PublicRouteTable",
            vpc_id=vpc.attr_vpc_id
        )
        public_route = ec2.CfnRoute(
            self,
            "PublicRoute",
            route_table_id=public_route_table.attr_route_table_id,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        public_subnet_route_table_association = ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnetRouteTableAssociation",
            subnet_id=public_subnet.attr_subnet_id,
            route_table_id=public_route_table.attr_route_table_id
        )
        security_group = ec2.CfnSecurityGroup(
            self,
            "SecurityGroup",
            group_description="Security group for ECS Cluster",
            vpc_id=vpc.attr_vpc_id
        )

        container_repo = ecr.CfnRepository(
            self,
            "ContainerRepo",
            repository_name=ecr_repo_name
        )
        ecs_cluster = ecs.CfnCluster(
            self,
            "ECSCluster"
        )
        ecs_task_execution_role = iam.CfnRole(
            self,
            "ECSTaskExecutionRole",
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ecs-tasks.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            policies=[
                iam.CfnRole.PolicyProperty(
                    policy_name="ECSTaskExecutionPolicy",
                    policy_document=iam.PolicyDocument(
                        statements=[
                            iam.PolicyStatement(
                                actions=[
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents",
                                    "ecr:*"
                                ],
                                resources=["*"],
                                effect=iam.Effect.ALLOW
                            )
                        ]
                    )
                )
            ]
        )
        ecs_log_group = logs.CfnLogGroup(
            self,
            "ECSLogGroup",
            log_group_name="/ecs/hello-world-task-000"
        )
        ecs_task_definition = ecs.CfnTaskDefinition(
            self,
            "ECSTaskDefinition",
            cpu="256",
            memory="512",
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            execution_role_arn=ecs_task_execution_role.attr_arn,
            container_definitions=[
                ecs.CfnTaskDefinition.ContainerDefinitionProperty(
                    name="hello-world-container",
                    image=f"{container_repo.attr_repository_uri}:latest",
                    essential=True,
                    log_configuration=ecs.CfnTaskDefinition.LogConfigurationProperty(
                        log_driver="awslogs",
                        options={
                            "awslogs-group": ecs_log_group.log_group_name,
                            "awslogs-region": "us-east-2",
                            "awslogs-stream-prefix": "TEST0000"
                        }
                    )
                )
            ]
        )
        
        codebuild_bucket = s3.Bucket(
            self, 
            "CodeBuildBucket"
        )
        codebuild_role = iam.CfnRole(
            self,
            "CodeBuildRole",
            role_name="CodeBuildRole-stack",
            assume_role_policy_document=iam.PolicyDocument(
                statements = [
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.ServicePrincipal("codebuild.amazonaws.com")
                        ],
                        actions=[
                            "sts:AssumeRole"
                        ]
                    )
                ]
            ),
            policies=[
                iam.CfnRole.PolicyProperty(
                    policy_name="CodeBuildPolicy",
                    policy_document=iam.PolicyDocument(
                        statements=[
                            iam.PolicyStatement(
                                effect=iam.Effect.ALLOW,
                                actions=[
                                    "ecr:*"
                                ],
                                resources=[container_repo.attr_arn]
                            ),
                            iam.PolicyStatement(
                                effect=iam.Effect.ALLOW,
                                actions=[
                                    "logs:CreateLogStream",
                                    "logs:CreateLogGroup",
                                    "logs:PutLogEvents",
                                    "ecr:GetAuthorizationToken"
                                ],
                                resources=["*"]
                            ),
                            iam.PolicyStatement(
                                effect=iam.Effect.ALLOW,
                                actions=[
                                    "s3:Get*",
                                    "s3:List*"
                                ],
                                resources=[
                                    codebuild_bucket.bucket_arn,
                                    f"{codebuild_bucket.bucket_arn}/*"
                                ]
                            )
                        ]
                    )
                )
            ]
        )
        docker_builder = codebuild.CfnProject(
            self,
            "DockerBuilder",
            source=codebuild.CfnProject.SourceProperty(
                type="S3",
                location=f"{codebuild_bucket.bucket_name}/.engine/",
                build_spec="buildspec.yml"
            ),
            artifacts=codebuild.CfnProject.ArtifactsProperty(
                type="S3",
                location=codebuild_bucket.bucket_name
            ),
            environment=codebuild.CfnProject.EnvironmentProperty(
                type="LINUX_CONTAINER",
                compute_type="BUILD_GENERAL1_SMALL",
                image="aws/codebuild/standard:4.0",
                privileged_mode=True,
                environment_variables=[
                    codebuild.CfnProject.EnvironmentVariableProperty(
                        name="IMAGE_TAG",
                        value="latest"
                    ),
                    codebuild.CfnProject.EnvironmentVariableProperty(
                        name="AWS_DEFAULT_REGION",
                        value=self.region
                    ),
                    codebuild.CfnProject.EnvironmentVariableProperty(
                        name="ECR_REPO_URI",
                        value=container_repo.attr_repository_uri
                    ),
                    codebuild.CfnProject.EnvironmentVariableProperty(
                        name="IMAGE_REPO_NAME",
                        value=ecr_repo_name
                    ),
                    codebuild.CfnProject.EnvironmentVariableProperty(
                        name="AWS_ACCOUNT_ID",
                        value="734818840861"
                    )
                ]
            ),
            service_role=codebuild_role.attr_arn
        )

        filesystem = s3.Bucket(
            self,
            "FileSystem"
        )

        CfnOutput(
            self,
            "ClusterName",
            value=ecs_cluster.attr_arn
        )
        CfnOutput(
            self,
            "TaskName",
            value=ecs_task_definition.attr_task_definition_arn
        )
        CfnOutput(
            self,
            "SecurityGroupID",
            value=security_group.attr_group_id
        )
        CfnOutput(
            self,
            "FileSystemName",
            value=filesystem.bucket_name
        )
        CfnOutput(
            self,
            "CodeBuildBucketName",
            value=codebuild_bucket.bucket_name
        )
        CfnOutput(
            self,
            "DockerBuilderName",
            value=docker_builder.attr_arn.split('/')[-1]
        )
        
        CfnOutput(
            self,
            "ContainerRepoName",
            value=ecr_repo_name
        )
        CfnOutput(
            self,
            "VpcId",
            value=vpc.attr_vpc_id
        )
        CfnOutput(
            self,
            "PublicSubnetId",
            value=public_subnet.attr_subnet_id
        )


class BuildModule(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(self, "CodeBucket")
        # bucket = s3.CfnBucket(self, "CodeBucket")