from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    aws_iam as iam
)
from constructs import Construct
import aws_cdk.aws_apigateway as apigateway
from aws_cdk import aws_lambda as _lambda

class EtEngineApiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        tbl_name = 'UserResourceLog'

        # Define the DynamoDB table
        my_table = dynamodb.Table(
            self, tbl_name,
            table_name=tbl_name,
            partition_key=dynamodb.Attribute(
                name='UserID',
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY  # You can adjust this based on your cleanup strategy
        )


        # Create an API Gateway
        rest_api = apigateway.RestApi(
            self, 'ETEngineAPI',
            rest_api_name='ETEngineAPI',
            description='Core API for provisioning resources and running algorithms'
        )

        provision = rest_api.root.add_resource('provision')
        provision_lambda = _lambda.Function(
            self, 'ProvisionLambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='provision.handler',
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
        )
        provision.add_method(
            'POST',
            integration=apigateway.LambdaIntegration(provision_lambda),
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
        provision_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:CreateStack', 
                    's3:CreateBucket', 
                    'ecr:CreateRepository',
                    'ecr:DeleteRepository',
                    'ecs:DescribeClusters',
                    'ecs:CreateCluster',
                    'ecs:DeleteCluster',
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
        # Give table access to the lambda
        my_table.grant_write_data(provision_lambda)

        

        

        # Create a resource
        hello_resource = rest_api.root.add_resource('hello')
        hello_lambda = _lambda.Function(
            self, 'HelloLambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='hello.handler',
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
        )
        hello_resource.add_method(
            'GET',
            integration=apigateway.LambdaIntegration(hello_lambda),
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

