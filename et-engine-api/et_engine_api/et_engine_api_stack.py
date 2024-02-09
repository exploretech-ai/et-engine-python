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

class EtEngineApiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.table = self.add_table('UserResourceLog')
        
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
        

        # Create an API Gateway
        self.api = apigateway.RestApi(
            self, 'ETEngineAPI',
            rest_api_name='ETEngineAPI',
            description='Core API for provisioning resources and running algorithms'
        )

        provision_lambda = self.add_method('provision', 'POST', table_access = "write")
        execute_lambda = self.add_method('execute', 'POST', table_access = "read")
        destroy_lambda = self.add_method('destroy', 'POST', table_access = "read", duration=30)
        status_lambda = self.add_method('status', 'GET', table_access = "read")
        configure_lambda = self.add_method('configure', 'POST', table_access = "read", duration=30)


        provision_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:CreateStack', 
                    'codebuild:CreateProject',
                    'codebuild:DeleteProject',
                    's3:CreateBucket', 
                    's3:DeleteBucket',
                    'ec2:CreateVpc',
                    'ec2:DeleteVpc',
                    'ec2:CreateTags',
                    'ec2:DeleteTags',
                    'ec2:DescribeVpcs',
                    'ec2:ModifyVpcAttribute',
                    'ec2:CreateSubnet',
                    'ec2:DeleteSubnet',
                    'ec2:DescribeSubnets',
                    'ec2:CreateSecurityGroup',
                    'ec2:DeleteSecurityGroup',
                    'ec2:DescribeSecurityGroups',
                    'ecr:CreateRepository',
                    'ecr:DeleteRepository',
                    'ecr:DescribeRepositories',
                    'ecs:DescribeClusters',
                    'ecs:CreateCluster',
                    'ecs:DeleteCluster',
                    'ecs:DeregisterTaskDefinition',
                    'ecs:RegisterTaskDefinition',
                    'iam:CreateRole',
                    'iam:PutRolePolicy',
                    'iam:GetRole',
                    'iam:DeleteRole',
                    'iam:PassRole',
                    'iam:DeleteRolePolicy',
                    'iam:CreateServiceLinkedRole',
                    'iam:DeleteServiceLinkedRole',
                    'logs:DeleteLogGroup'
                ],
                resources=['*'],
            )
        )
        execute_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'ecs:RunTask',
                    'iam:PassRole',
                    'cloudformation:DescribeStacks'
                ],
                resources=['*'],
            )
        )
        destroy_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:DeleteBucket',
                    's3:ListBucket',
                    's3:DeleteObject',
                    'cloudformation:DeleteStack',
                    'cloudformation:DescribeStacks',
                    'codebuild:DeleteProject',
                    'ec2:DeleteSecurityGroup',
                    'ecr:DeleteRepository',
                    'ec2:DeleteSubnet',
                    'ec2:DeleteVpc',
                    'ec2:DescribeSubnets',
                    'ec2:DescribeVpcs',
                    'ecs:DeregisterTaskDefinition',
                    'ecs:DescribeClusters',
                    'ecs:DeleteCluster',
                    'iam:DeleteRolePolicy',
                    'iam:DeleteRole',
                    'logs:DeleteLogGroup',
                    'ecr:DescribeImages',
                    'ecr:BatchGetImage',
                    'ecr:ListImages',
                    'ecr:BatchDeleteImage'

                ],
                resources=['*'],
            )
        )
        status_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions = [
                    'cloudformation:DescribeStacks'
                ],
                resources=['*']
            )
        )
        configure_lambda.add_to_role_policy(
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


    def add_method(self, name, request_type, table_access = None, duration = 3):
        """
        name: base name of the method, needs to be in folder named 'lambda' with a handler method
        type: 'POST', 'GET', etc.

        """
        method = self.api.root.add_resource(name)
        method_lambda = _lambda.Function(
            self, name + 'Lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= name + '.handler',
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(duration)
        )
        method.add_method(
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
        
        if table_access == "read":
            self.table.grant_read_data(method_lambda)
        elif table_access == "write":
            self.table.grant_write_data(method_lambda)

        return method_lambda
    
    def add_table(self, tbl_name):
        return dynamodb.Table(
            self, tbl_name,
            table_name=tbl_name,
            partition_key=dynamodb.Attribute(
                name='UserID',
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY  # You can adjust this based on your cleanup strategy
        )
    
    def add_bucket(self, name):
        return s3.Bucket(self, name)