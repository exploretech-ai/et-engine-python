
from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


class TaskMethods(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, api, key_authorizer, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        tasks = api.root.add_resource("tasks")
        tasks_list_lambda = _lambda.Function(
            self,
            "tasks-list",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tasks.list.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        tasks.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(tasks_list_lambda),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Content-Type': True,
                },
                'responseModels': {
                    'application/json': apigateway.Model.EMPTY_MODEL,
                },
            }],
            authorizer = key_authorizer,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
        )
        database.grant_access(tasks_list_lambda)

        tasks_clear_lambda = _lambda.Function(
            self,
            "tasks-clear",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tasks.clear.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        tasks.add_method(
            "DELETE",
            integration=apigateway.LambdaIntegration(tasks_clear_lambda),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Content-Type': True,
                },
                'responseModels': {
                    'application/json': apigateway.Model.EMPTY_MODEL,
                },
            }],
            authorizer = key_authorizer,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
        )
        database.grant_access(tasks_clear_lambda)


        task_id = tasks.add_resource("{taskID}")
        task_id_status_lambda = _lambda.Function(
            self,
            "tasks-status",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tasks.status.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.minutes(3),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        task_id.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(task_id_status_lambda),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Content-Type': True,
                },
                'responseModels': {
                    'application/json': apigateway.Model.EMPTY_MODEL,
                },
            }],
            authorizer = key_authorizer,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
        )
        database.grant_access(task_id_status_lambda)
        task_id_status_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'ecs:*',
                ],
                resources=['*']
            )
        )