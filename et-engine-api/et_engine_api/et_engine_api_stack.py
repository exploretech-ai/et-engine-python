from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    aws_iam as iam,
    aws_s3 as s3,
    aws_apigateway as apigateway,
    aws_s3_deployment as s3_deploy,
    aws_lambda as _lambda
)
from constructs import Construct

class MasterDB(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        self.algorithms = dynamodb.Table(
            self, 
            "Algorithms",
            partition_key=dynamodb.Attribute(
                name='algoID',
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY  # You can adjust this based on your cleanup strategy
        )

        self.users = dynamodb.Table(
            self,
            "Users",
            partition_key=dynamodb.Attribute(
                name='userID',
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY  # You can adjust this based on your cleanup strategy
        )

class API(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an API Gateway
        self.api = apigateway.RestApi(
            self, 'API',
            rest_api_name='ETEngineAPI',
            description='Core API for provisioning resources and running algorithms'
        )
        
        algorithms = self.api.root.add_resource("algorithms")
        
        algorithms_lambda = self.add_lambda(algorithms, "POST", "algorithms", "algorithms.new.handler")        
        database.algorithms.grant_write_data(algorithms_lambda)
        algorithms_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'dynamodb:PutItem',
                    'cloudformation:DescribeStacks'
                ],
                resources=['*']
            )
        )
        
        # self.add_lambda(algorithms, "GET", "algorithms", "algorithms.list.handler")

        algorithms_id = algorithms.add_resource("{id}")
        algorithms_id_lambda = self.add_lambda(algorithms_id, "GET", "algorithm", "algorithms.algorithm.info.handler")        
        database.algorithms.grant_read_data(algorithms_id_lambda)
        algorithms_id_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'dynamodb:GetItem',
                    'cloudformation:DescribeStacks'
                ],
                resources=['*']
            )
        )

        algorithms_provision = algorithms_id.add_resource("provision")
        algorithms_provision_lambda = self.add_lambda(algorithms_provision, "POST", "provision", "algorithms.provision.provision.handler")
        algorithms_provision_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:*',
                    'iam:*',
                    'log-group:*',
                    'ec2:*',
                    'ecr:*',
                    'ecs:*',
                    's3:*',
                    'codebuild:*'
                ],
                resources=['*']
            )
        )


        # algorithms_provision_status = algorithms_provision.add_resource("status")
        algorithms_provision_status_lambda = self.add_lambda(algorithms_provision, "GET", "provision-status", "algorithms.provision.status.handler")
        algorithms_provision_status_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions = [
                    'cloudformation:DescribeStacks'
                ],
                resources=["*"]
            )
        )


        algorithms_build = algorithms_id.add_resource("build")
        algorithms_build_lambda = self.add_lambda(algorithms_build, 'POST', 'build', "algorithms.build.build.handler", duration=30)
        algorithms_build_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions = [
                    'cloudformation:DescribeStacks',
                    's3:PutObject',
                    's3:ListBucket',
                    's3:GetObject',
                    'codebuild:StartBuild'
                ],
                resources = ['*']
            )
        )
        algorithms_build_status_lambda = self.add_lambda(algorithms_build, "GET", "build-status", "algorithms.destroy.status.handler")

        algorithms_execute = algorithms_id.add_resource("execute")
        algorithms_execute_lambda = self.add_lambda(algorithms_execute, "POST", "execute", "algorithms.execute.execute.handler")
        algorithms_execute_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:DescribeStacks',
                    'ecs:RunTask',
                    'iam:PassRole'
                ],
                resources=["*"]
            )
        )
        algorithms_execute_status_lambda = self.add_lambda(algorithms_execute, "GET", "execute-status", "algorithms.execute.status.handler")

        algorithms_destroy = algorithms_id.add_resource("destroy")
        algorithms_destroy_lambda = self.add_lambda(algorithms_destroy, "POST", "destroy", "algorithms.destroy.destroy.handler", duration = 30)
        algorithms_destroy_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:Delete*',
                    's3:ListBucket',
                    'cloudformation:DeleteStack',
                    'cloudformation:DescribeStacks',
                    'codebuild:DeleteProject',
                    'ec2:*',
                    'ecr:Delete*',
                    'ecs:DeregisterTaskDefinition',
                    'ecs:DescribeClusters',
                    'iam:Delete*',
                    'ecs:Delete*',
                    'logs:DeleteLogGroup',
                    'ecr:DescribeImages',
                    'ecr:BatchGetImage',
                    'ecr:ListImages',
                    'ecr:BatchDeleteImage'

                ],
                resources=['*'],
            )
        )
        algorithms_destroy_status_lambda = self.add_lambda(algorithms_destroy, "GET", "destroy-status", "algorithms.destroy.status.handler")

        algorithms_filesystem = algorithms_id.add_resource("filesystem")
        algorithms_filesystem.add_method('GET')
        algorithms_filesystem.add_method('POST')

    def add_lambda(self, resource, request_type, method_prefix, handler, duration = 3):
        """
        name: base name of the method, needs to be in folder named 'lambda' with a handler method
        type: 'POST', 'GET', etc.

        """

        method_lambda = _lambda.Function(
            self, method_prefix + '-' + request_type,
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= handler,
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(duration)
        )
        resource.add_method(
            request_type,
            integration=apigateway.LambdaIntegration(method_lambda),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Content-Type': True,
                },
                'responseModels': {
                    'application/json': apigateway.Model.EMPTY_MODEL,
                },
            }],
        )
        
        return method_lambda

        # algorithms_computestack = algorithms_id.add_resource("computestack")

class Templates(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.dockerbuild_template = s3.Bucket(self, 'et-engine-dockerbuild-template')
        self.dockerbuild_template_contents = s3_deploy.BucketDeployment(
            self, 
            'et-engine-dockerbuild-template-deploy', 
            sources=[s3_deploy.Source.asset('./engine-dockerbuild-template')],
            destination_bucket=self.dockerbuild_template,
            retain_on_delete=False
        )
        self.dockerbuild_template_output = CfnOutput(
            self,
            'DockerBuildTemplate',
            value = self.dockerbuild_template.bucket_name
        )
        
class ETEngine(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.database = MasterDB(self, "MasterDB")
        self.api = API(self, "API", self.database)
        self.templates = Templates(self, "Templates")

        CfnOutput(
            self, 
            'AlgorithmDB',
            value = self.database.algorithms.table_name
        )
        CfnOutput(
            self,
            "TemplateBucket",
            value = self.templates.dockerbuild_template.bucket_name
        )



        # algorithm_id_lambda = self.add_method("{algo_id}", "")

        # provision_lambda = self.add_method('provision', 'POST', table_access = "write")
        # execute_lambda = self.add_method('execute', 'POST', table_access = "read")
        # destroy_lambda = self.add_method('destroy', 'POST', table_access = "read", duration=30)
        # status_lambda = self.add_method('status', 'GET', table_access = "read")
        # configure_lambda = self.add_method('configure', 'POST', table_access = "read", duration=30)


        # provision_lambda.add_to_role_policy(
        #     iam.PolicyStatement(
        #         actions=[
        #             'cloudformation:CreateStack', 
        #             'codebuild:CreateProject',
        #             'codebuild:DeleteProject',
        #             's3:CreateBucket', 
        #             's3:DeleteBucket',
        #             'ec2:*',
        #             'ecr:CreateRepository',
        #             'ecr:DeleteRepository',
        #             'ecr:DescribeRepositories',
        #             'ecs:DescribeClusters',
        #             'ecs:CreateCluster',
        #             'ecs:DeleteCluster',
        #             'ecs:DeregisterTaskDefinition',
        #             'ecs:RegisterTaskDefinition',
        #             'iam:CreateRole',
        #             'iam:PutRolePolicy',
        #             'iam:GetRole',
        #             'iam:DeleteRole',
        #             'iam:PassRole',
        #             'iam:DeleteRolePolicy',
        #             'iam:CreateServiceLinkedRole',
        #             'iam:DeleteServiceLinkedRole',
        #             'logs:DeleteLogGroup'
        #         ],
        #         resources=['*'],
        #     )
        # )
        # execute_lambda.add_to_role_policy(
        #     iam.PolicyStatement(
        #         actions=[
        #             'ecs:RunTask',
        #             'iam:PassRole',
        #             'cloudformation:DescribeStacks'
        #         ],
        #         resources=['*'],
        #     )
        # )
        # destroy_lambda.add_to_role_policy(
        #     iam.PolicyStatement(
        #         actions=[
        #             's3:DeleteBucket',
        #             's3:ListBucket',
        #             's3:DeleteObject',
        #             'cloudformation:DeleteStack',
        #             'cloudformation:DescribeStacks',
        #             'codebuild:DeleteProject',
        #             'ec2:*',
        #             'ecr:DeleteRepository',
        #             'ecs:DeregisterTaskDefinition',
        #             'ecs:DescribeClusters',
        #             'ecs:DeleteCluster',
        #             'iam:DeleteRolePolicy',
        #             'iam:DeleteRole',
        #             'logs:DeleteLogGroup',
        #             'ecr:DescribeImages',
        #             'ecr:BatchGetImage',
        #             'ecr:ListImages',
        #             'ecr:BatchDeleteImage'

        #         ],
        #         resources=['*'],
        #     )
        # )
        # status_lambda.add_to_role_policy(
        #     iam.PolicyStatement(
        #         actions = [
        #             'cloudformation:DescribeStacks'
        #         ],
        #         resources=['*']
        #     )
        # )
        # configure_lambda.add_to_role_policy(
        #     iam.PolicyStatement(
        #         actions = [
        #             'cloudformation:DescribeStacks',
        #             's3:PutObject',
        #             's3:ListBucket',
        #             's3:GetObject',
        #             'codebuild:StartBuild'
        #         ],
        #         resources = ['*']
        #     )
        # )


    
    
    def add_table(self, tbl_name):
        return dynamodb.Table(
            self, tbl_name,
            table_name=tbl_name,
            partition_key=dynamodb.Attribute(
                name='AlgoID',
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY  # You can adjust this based on your cleanup strategy
        )
    
    def add_bucket(self, name):
        return s3.Bucket(self, name)