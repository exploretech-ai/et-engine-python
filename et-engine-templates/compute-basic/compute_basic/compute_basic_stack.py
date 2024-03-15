from aws_cdk import (
    Stack,
    CfnOutput,
    CfnParameter,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_logs as logs,
    aws_s3 as s3,
    aws_codebuild as codebuild,
    aws_lambda as _lambda,
    aws_s3_notifications as s3n
)
from constructs import Construct
import aws_cdk as cdk

class ComputeBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # >>>>> PARAMETERS
        # tool-id
        tool_id = CfnParameter(
            self,
            "toolID"
        ).value_as_string

        # VPC needs to be a global variable and vpc.attr_vpc_id needs to be accessed here
        #     - Only 5 VPC's per region are allowed and 200 subnets are allowed per region
        #     - ecs.run_task() needs subnet and security group id, which can be accessed by querying the stack by its name and its outputs

        # The LAMBDA codebuild trigger needs to be defined externally and referenced here
        # <<<<<

        code_bucket = s3.Bucket(
            self,
            "CodeBucket",
            bucket_name = "tool-" + tool_id,
            # auto_delete_objects = True,
            # removal_policy = cdk.RemovalPolicy.DESTROY
        )
        codebuild_trigger = _lambda.Function(
            self, 'codebuild-trigger',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code = _lambda.InlineCode("""
import boto3
def handler(event, context):
    print("hello, world")
    tool = event['Records'][0]['s3']['bucket']['name']
    codebuild = boto3.client('codebuild')
    codebuild.start_build(projectName=tool)
            """),
            handler = "index.handler"
        )
        codebuild_trigger.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'codebuild:StartBuild'
                ],
                resources=['*']
            )
        )
        code_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, 
            s3n.LambdaDestination(codebuild_trigger)
        )


        # >>>>> THIS WILL NEED TO BE MOVED OUTSIDE THE TEMPLATE AND attr_vpc_id NEEDS TO BE IMPORTED AS A PARAMETER
        vpc = ec2.CfnVPC(
            self,
            "ClusterVPC",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            cidr_block="10.0.0.0/16"
        )
        # <<<<<

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
            repository_name="tool-" + tool_id
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
            log_group_name="/ecs/tool-" + tool_id
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
                    name="tool-" + tool_id,
                    image=f"{container_repo.attr_repository_uri}:latest",
                    essential=True,
                    log_configuration=ecs.CfnTaskDefinition.LogConfigurationProperty(
                        log_driver="awslogs",
                        options={
                            "awslogs-group": ecs_log_group.log_group_name,
                            "awslogs-region": "us-east-2",
                            "awslogs-stream-prefix": "tool-" + tool_id
                        }
                    )
                )
            ]
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
                                    code_bucket.bucket_arn,
                                    f"{code_bucket.bucket_arn}/*"
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
            name = "tool-" + tool_id,
            source=codebuild.CfnProject.SourceProperty(
                type="S3",
                location=f"{code_bucket.bucket_name}/tool.zip"
            ),
            artifacts=codebuild.CfnProject.ArtifactsProperty(
                type="S3",
                location=code_bucket.bucket_name
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
                        value="tool-"+tool_id
                    ),
                    codebuild.CfnProject.EnvironmentVariableProperty(
                        name="AWS_ACCOUNT_ID",
                        value="734818840861"
                    )
                ]
            ),
            service_role=codebuild_role.attr_arn
        )

        # CfnOutput(
        #     self,
        #     "ClusterName",
        #     value=ecs_cluster.attr_arn
        # )
        # CfnOutput(
        #     self,
        #     "TaskName",
        #     value=ecs_task_definition.attr_task_definition_arn
        # )
        # CfnOutput(
        #     self,
        #     "SecurityGroupID",
        #     value=security_group.attr_group_id
        # )
        # CfnOutput(
        #     self,
        #     "FileSystemName",
        #     value=filesystem.bucket_name
        # )
        # CfnOutput(
        #     self,
        #     "CodeBuildBucketName",
        #     value=codebuild_bucket.bucket_name
        # )
        # CfnOutput(
        #     self,
        #     "DockerBuilderName",
        #     value=docker_builder.attr_arn.split('/')[-1]
        # )
        
        # CfnOutput(
        #     self,
        #     "ContainerRepoName",
        #     value="tool-"+tool_id
        # )
        # CfnOutput(
        #     self,
        #     "VpcId",
        #     value=vpc.attr_vpc_id
        # )
        # CfnOutput(
        #     self,
        #     "PublicSubnetId",
        #     value=public_subnet.attr_subnet_id
        # )
