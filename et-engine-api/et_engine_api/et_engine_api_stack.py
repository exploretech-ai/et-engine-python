from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy
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
            self, 'SimpleRestApi',
            rest_api_name='SimpleRestApi',
            description='A simple REST API'
        )


        new_resource = rest_api.root.add_resource('new')
        new_lambda = _lambda.Function(
            self, 'NewResourceLambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='create_resource.handler',
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
        )
        new_resource.add_method(
            'POST',
            integration=apigateway.LambdaIntegration(new_lambda),
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

        # Give table access to the lambda
        my_table.grant_write_data(new_lambda)

        

        

        # Create a resource
        hello_resource = rest_api.root.add_resource('hello')

        hello_lambda = _lambda.Function(
            self, 'HelloLambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler='hello.handler',
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
        )

        # Add a method to the resource
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

