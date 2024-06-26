
from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
)
from constructs import Construct


class ApiKeyMethods(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, api, authorizer, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        keys = api.root.add_resource("keys")
        keys_create_lambda = _lambda.Function(
            self, 'keys-create-lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "keys.create.handler",
            code=_lambda.Code.from_asset('lambda'),
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        keys.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(keys_create_lambda),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Content-Type': True,
                },
                'responseModels': {
                    'application/json': apigateway.Model.EMPTY_MODEL,
                },
            }],
            authorizer = authorizer,
            authorization_type = apigateway.AuthorizationType.COGNITO,
        )
        database.grant_access(keys_create_lambda)
        
        keys_list_lambda = _lambda.Function(
            self, 'keys-list-lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "keys.list.handler",
            code=_lambda.Code.from_asset('lambda'),
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        keys.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(keys_list_lambda),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Content-Type': True,
                },
                'responseModels': {
                    'application/json': apigateway.Model.EMPTY_MODEL,
                },
            }],
            authorizer = authorizer,
            authorization_type = apigateway.AuthorizationType.COGNITO,
        )
        database.grant_access(keys_list_lambda)

        # keys_delete_lambda
        keys_delete_lambda = _lambda.Function(
            self, 'keys-delete-lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "keys.delete.handler",
            code=_lambda.Code.from_asset('lambda'),
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        keys.add_method(
            "DELETE",
            integration=apigateway.LambdaIntegration(keys_delete_lambda),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Content-Type': True,
                },
                'responseModels': {
                    'application/json': apigateway.Model.EMPTY_MODEL,
                },
            }],
            authorizer = authorizer,
            authorization_type = apigateway.AuthorizationType.COGNITO,
        )
        database.grant_access(keys_delete_lambda)
