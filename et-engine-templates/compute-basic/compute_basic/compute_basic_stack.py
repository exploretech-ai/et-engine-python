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
    aws_s3_notifications as s3n,
    aws_ecs_patterns as ecs_patterns
)
from constructs import Construct
import aws_cdk as cdk

class ComputeBasicStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # PARAMETERS
        tool_id = CfnParameter(
            self,
            "toolID"
        ).value_as_string

        # Bucket & Build Trigger
        code_bucket = s3.Bucket(
            self,
            "CodeBucket",
            bucket_name = "tool-" + tool_id,
            auto_delete_objects = True,
            removal_policy = cdk.RemovalPolicy.DESTROY
        )
        
        # THIS CODE SHOULD BE SOMEWHERE ELSE SO WE DON'T NEED A TON OF LAMBDA FUNCTIONS
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
            s3n.LambdaDestination(codebuild_trigger),
            s3.NotificationKeyFilter(
                prefix="tool.tar.gz"
            )
        )

        # Container Image
        container_repo = ecr.Repository(
            self,
            "ContainerRepo",
            repository_name="tool-" + tool_id
        )

        # Codebuild Project
        build_spec = codebuild.BuildSpec.from_object({
            "version": "0.2",
            "phases": {
                "pre_build": {
                    "commands": [
                        "echo Logging in to Amazon ECR...",
                        "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com",
                        "echo Downloading the image archive from S3...",
                        "aws s3 cp s3://$BUCKET_NAME/tool.tar.gz tool.tar.gz"
                    ]
                },
                "build": {
                    "commands": [
                        "echo Build started on `date`",
                        "echo Extracting the Docker image...",
                        "IMAGE_NAME=$(docker load --input tool.tar.gz)",
                        'IMAGE_NAME=${IMAGE_NAME#"Loaded image: "}',
                        "echo Tagging $IMAGE_NAME",
                        "docker tag $IMAGE_NAME $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG"
                    ]
                },
                "post_build": {
                    "commands": [
                        "echo Build completed on `date`",
                        "echo Pushing the Docker image...",
                        "docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG"
                    ]
                }
            }
        })
        docker_builder = codebuild.Project(
            self,
            "DockerBuilder",
            project_name = "tool-" + tool_id,
            build_spec = build_spec,
            environment=codebuild.BuildEnvironment(
                privileged=True,
                environment_variables={
                    "IMAGE_TAG": codebuild.BuildEnvironmentVariable(
                        value="latest"
                    ),
                    "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(
                        value=self.region
                    ),
                    "ECR_REPO_URI": codebuild.BuildEnvironmentVariable(
                        value=container_repo.repository_uri
                    ),
                    "IMAGE_REPO_NAME": codebuild.BuildEnvironmentVariable(
                        value="tool-"+tool_id
                    ),
                    "AWS_ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                        value="734818840861"
                    ),
                    "BUCKET_NAME": codebuild.BuildEnvironmentVariable(
                        value="tool-"+tool_id
                    )
                },
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0
            ),
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
        )
        docker_builder.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'ecr:*'
                ],
                resources=["*"]
            )
        )
        docker_builder.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*'
                ],
                resources=[
                    code_bucket.bucket_arn,
                    code_bucket.bucket_arn + "/*"
                ]
            )
        )
        container_repo.grant_push(docker_builder)

