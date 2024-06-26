from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


class ToolMethods(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, api, key_authorizer, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        tools = api.root.add_resource("tools")
        tools_create_lambda = _lambda.Function(
            self, 'tools-create',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.create.handler",
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
        tools.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(tools_create_lambda),
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
        database.grant_access(tools_create_lambda)
        tools_create_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:CreateStack',
                    'ssm:GetParameters',
                    's3:*',
                    'ec2:*',
                    'iam:*',
                    'ecr:CreateRepository',
                    'ecr:DeleteRepository',
                    'ecr:DescribeRepositories',
                    'ecs:*',
                    'elasticloadbalancing:*',
                    'iam:*',
                    'logs:DescribeLogGroups',
                    'logs:DeleteLogGroup',
                    'codebuild:CreateProject',
                    'codebuild:DeleteProject',
                    'lambda:CreateFunction',
                    'lambda:DeleteFunction',
                    'lambda:GetFunction',
                    'lambda:AddPermission',
                    'lambda:RemovePermission',
                    'lambda:InvokeFunction',
                ],
                resources=['*']
            )
        )

        tools_list_lambda = _lambda.Function(
            self, 'tools-list',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.list.handler",
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
        tools.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(tools_list_lambda),
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
        database.grant_access(tools_list_lambda)

        tools_delete_lambda = _lambda.Function(
            self, 'tools-delete',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.delete.handler",
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
        tools.add_method(
            "DELETE",
            integration=apigateway.LambdaIntegration(tools_delete_lambda),
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
        database.grant_access(tools_delete_lambda)
        tools_delete_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:ListBucket',
                    's3:DeleteObject',
                    's3:DeleteBucket',
                    's3:*',
                    'ecs:*',
                    'ecr:ListImages',
                    'ecr:DeleteImage',
                    'ecr:BatchDeleteImage',
                    'ecr:DescribeRepositories',
                    'ecr:DeleteRepository',
                    'cloudformation:DeleteStack',
                    'cloudformation:DescribeStacks',
                    'codebuild:DeleteProject',
                    'logs:DeleteLogGroup',
                    'lambda:InvokeFunction',
                    'lambda:RemovePermission',
                    'lambda:DeleteFunction',
                    'iam:DeleteRolePolicy',
                    'iam:DetachRolePolicy',
                    'iam:DeleteRole'

                ],
                resources=['*']
            )
        )


        tools_id = tools.add_resource("{toolID}")
        tools_upload_lambda = _lambda.Function(
            self, 'tools-upload',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.push.handler",
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
        tools_id.add_method(
            "PUT",
            integration=apigateway.LambdaIntegration(tools_upload_lambda),
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
        database.grant_access(tools_upload_lambda)
        tools_upload_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:PutObject'
                ],
                resources=['*']
            )
        )

        tools_execute_lambda = _lambda.Function(
            self, 'tools-execute',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.execute.handler",
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
        tools_id.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(tools_execute_lambda),
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
        database.grant_access(tools_execute_lambda)
        tools_execute_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:DescribeStacks',
                    'ecs:RunTask',
                    'iam:PassRole',
                    'ecs:RegisterTaskDefinition',
                    'ecr:*',
                    'elasticfilesystem:*',
                ],
                resources=['*']
            )
        )

        tools_describe_lambda = _lambda.Function(
            self, 'tools-describe',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.describe.handler",
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
        tools_id.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(tools_describe_lambda),
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
        database.grant_access(tools_describe_lambda)
        tools_describe_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'codebuild:ListBuildsForProject',
                    'codebuild:BatchGetBuilds',
                    'ecr:DescribeImages'
                ],
                resources=['*']
            )
        )

        tools_id_share = tools_id.add_resource("share")
        tools_id_share_lambda = _lambda.Function(
            self, 'tools-share',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.share.handler",
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
        tools_id_share.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(tools_id_share_lambda),
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
        database.grant_access(tools_id_share_lambda)