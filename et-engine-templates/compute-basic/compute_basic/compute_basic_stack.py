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
        sg_id = CfnParameter(
            self,
            "sgID"
        ).value_as_string
        vpc_id = CfnParameter(
            self,
            "vpc"
        ).value_as_string
        subnet_id = CfnParameter(
            self,
            "subnetID"
        ).value_as_string
        cluster_name = CfnParameter(
            self,
            "clusterARN"
        ).value_as_string
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


        container_repo = ecr.CfnRepository(
            self,
            "ContainerRepo",
            repository_name="tool-" + tool_id
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

        CfnOutput(
            self,
            "ClusterName",
            value=cluster_name
        )
        CfnOutput(
            self,
            "TaskName",
            value=ecs_task_definition.attr_task_definition_arn
        )
        CfnOutput(
            self,
            "SecurityGroupID",
            value=sg_id
        )
        CfnOutput(
            self,
            "VpcId",
            value=vpc_id
        )
        CfnOutput(
            self,
            "PublicSubnetId",
            value=subnet_id
        )

        # >>>>> This is a new parameter to test the stack update lambda
        CfnOutput(
            self,
            "TestString",
            value="test2"
        )
        # <<<<<
