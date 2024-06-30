
from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct
  
class VfsMethods(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, api, key_authorizer, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        vfs = api.root.add_resource("vfs")
        vfs_create_lambda = _lambda.Function(
            self, 'vfs-create',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.create.handler",
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
        vfs.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_create_lambda),
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
        database.grant_access(vfs_create_lambda)
        vfs_create_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*',
                    "cloudformation:CreateStack",
                    "elasticfilesystem:*",
                    "ec2:*",
                    "ssm:*",
                    'iam:*',
                    'lambda:*'
                ],
                resources=['*']
            )
        )

        vfs_list_lambda = _lambda.Function(
            self, 'vfs-list',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.list.handler",
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
        vfs.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(vfs_list_lambda),
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
        database.grant_access(vfs_list_lambda)

        vfs_delete_lambda = _lambda.Function(
            self, 'vfs-delete',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.delete.handler",
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
        vfs.add_method(
            "DELETE",
            integration=apigateway.LambdaIntegration(vfs_delete_lambda),
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
        database.grant_access(vfs_delete_lambda)
        vfs_delete_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*',
                    'cloudformation:*',
                    'efs:*',
                    'ec2:*',
                    'iam:*',
                    'lambda:*'
                ],
                resources=['*']
            )
        )


        vfs_id = vfs.add_resource("{vfsID}")
        vfs_upload_lambda = _lambda.Function(
            self, 'vfs-upload',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "upload.handler",
            code=_lambda.Code.from_asset('lambda/vfs'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        vfs_id.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_upload_lambda),
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
        database.grant_access(vfs_upload_lambda)
        vfs_upload_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*'
                ],
                resources=['*']
            )
        )
        
        vfs_download_lambda = _lambda.Function(
            self, 'vfs-download',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.download.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        vfs_id.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(vfs_download_lambda),
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
        database.grant_access(vfs_download_lambda)
        vfs_download_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:GetObject',
                    'lambda:*'
                ],
                resources=['*']
            )
        )

        vfs_id_list = vfs_id.add_resource("list")
        vfs_id_list_lambda = _lambda.Function(
            self, 'vfs-list-directory',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.directory.handler",
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
        vfs_id_list.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(vfs_id_list_lambda),
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
        database.grant_access(vfs_id_list_lambda)
        vfs_id_list_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:ListBucket',
                    'lambda:InvokeFunction'
                ],
                resources=['*']
            )
        )

        vfs_id_mkdir = vfs_id.add_resource("mkdir")
        vfs_id_mkdir_lambda = _lambda.Function(
            self, 'vfs-mkdir-directory',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.mkdir.handler",
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
        vfs_id_mkdir.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_id_mkdir_lambda),
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
        database.grant_access(vfs_id_mkdir_lambda)
        vfs_id_mkdir_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:ListBucket',
                    'lambda:InvokeFunction'
                ],
                resources=['*']
            )
        )

        vfs_id_share = vfs_id.add_resource("share")
        vfs_id_share_lambda = _lambda.Function(
            self, 'vfs-share',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.share.handler",
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
        vfs_id_share.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_id_share_lambda),
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
        database.grant_access(vfs_id_share_lambda)
        

        vfs_files = vfs_id.add_resource("files")
        vfs_file_path = vfs_files.add_resource("{filepath+}")
        vfs_file_delete_lambda = _lambda.Function(
            self, 'vfs-file-delete',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.files.delete.handler",
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
        vfs_file_path.add_method(
            "DELETE",
            integration=apigateway.LambdaIntegration(vfs_file_delete_lambda),
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
        database.grant_access(vfs_file_delete_lambda)
        vfs_file_delete_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'lambda:InvokeFunction'
                ],
                resources=['*']
            )
        )