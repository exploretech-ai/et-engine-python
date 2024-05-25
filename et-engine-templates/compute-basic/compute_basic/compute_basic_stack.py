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
        # cluster_arn = CfnParameter(
        #     self,
        #     "clusterARN"
        # ).value_as_string

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
            s3n.LambdaDestination(codebuild_trigger)
        )

        # Container Image
        container_repo = ecr.Repository(
            self,
            "ContainerRepo",
            repository_name="tool-" + tool_id
        )

        # Codebuild Project
        docker_builder = codebuild.Project(
            self,
            "DockerBuilder",
            project_name = "tool-" + tool_id,
            source=codebuild.Source.s3(
                bucket=code_bucket,
                path="tool.zip"
            ),
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
                resources=['*']
            )
        )
        container_repo.grant_push(docker_builder)


        # ==================================================================================================================
        # THESE WILL NEED TO BE REMOVED AND CONFIGURED ON THE FLY ALONG WITH EFS VOLUMES

        # ecs_task_definition = ecs.Ec2TaskDefinition(
        #     self,
        #     "ToolTask",
        #     family="tool-" + tool_id
        # )
        # ecs_task_definition.add_container(
        #     "ToolImage",
        #     image=ecs.ContainerImage.from_registry(
        #         container_repo.repository_uri + ':latest'
        #     ),
        #     memory_limit_mib=512,
        #     logging=ecs.LogDrivers.aws_logs(
        #         stream_prefix=f"tool-{tool_id}",
        #         mode=ecs.AwsLogDriverMode.NON_BLOCKING,
        #     ),
        #     container_name=f"tool-{tool_id}"
        # )
        # ecs_task_definition.add_to_execution_role_policy(
        #     iam.PolicyStatement(
        #         actions=[
        #             'ecr:*'
        #         ],
        #         resources=['*']
        #     )
        # )
        # ==================================================================================================================


        

        # OUTPUTS
        # CfnOutput(
        #     self,
        #     "ClusterName",
        #     value=cluster_arn
        # )
        # CfnOutput(
        #     self,
        #     "TaskName",
        #     value=ecs_task_definition.task_definition_arn
        # )
       