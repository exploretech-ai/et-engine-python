
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
    def __init__(self, scope: Construct, construct_id: str, database, api, key_authorizer, compute, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        method_responses = [{
            'statusCode': '200',
            'responseParameters': {
                'method.response.header.Content-Type': True,
            },
            'responseModels': {
                'application/json': apigateway.Model.EMPTY_MODEL,
            },
        }]
        database_subnets = ec2.SubnetSelection(
            subnets=database.vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ).subnets
        )

        vfs = api.root.add_resource("vfs")
        vfs_create_lambda = _lambda.Function(
            self, 'vfs-create',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.create.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=database_subnets,
            security_groups=[database.sg]
        )
        vfs.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_create_lambda),
            method_responses=method_responses,
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
            vpc_subnets=database_subnets,
            security_groups=[database.sg]
        )
        vfs.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(vfs_list_lambda),
            method_responses=method_responses,
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
            vpc_subnets=database_subnets,
            security_groups=[database.sg]
        )
        vfs.add_method(
            "DELETE",
            integration=apigateway.LambdaIntegration(vfs_delete_lambda),
            method_responses=method_responses,
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


        vfs_files = vfs_id.add_resource("files")
        vfs_file_path = vfs_files.add_resource("{filepath+}")
        
        vfs_upload_lambda = _lambda.Function(
            self, 'vfs-upload',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "upload.handler",
            code=_lambda.Code.from_asset('lambda/vfs'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=database_subnets,
            security_groups=[database.sg]
        )
        vfs_file_path.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_upload_lambda),
            method_responses=method_responses,
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

        forwarded_uri = "http://" + compute.download_files.load_balancer.load_balancer_dns_name + "/vfs/{vfsID}/files/{filepath}"
        integration = apigateway.Integration(
            type=apigateway.IntegrationType.HTTP_PROXY,
            uri=forwarded_uri,
            integration_http_method="ANY",
            options=apigateway.IntegrationOptions(
                connection_type=apigateway.ConnectionType.VPC_LINK,
                vpc_link=compute.download_files.vpc_link,
                request_parameters = {
                    "integration.request.path.vfsID": "method.request.path.vfsID",
                    "integration.request.path.filepath": "method.request.path.filepath"
                }
            )
        )
        vfs_file_path.add_method(
            "GET",
            integration=integration,
            method_responses=method_responses,
            authorizer = key_authorizer,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
            request_parameters={
                "method.request.path.vfsID": True,
                "method.request.path.filepath": True,
            },

        )
        
        vfs_file_delete_lambda = _lambda.Function(
            self, 'vfs-file-delete',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.files.delete.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=database_subnets,
            security_groups=[database.sg]
        )
        vfs_file_path.add_method(
            "DELETE",
            integration=apigateway.LambdaIntegration(vfs_file_delete_lambda),
            method_responses=method_responses,
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


        vfs_id_list = vfs_id.add_resource("list")
        vfs_list_path = vfs_id_list.add_resource("{filepath+}")

        vfs_id_list_lambda = _lambda.Function(
            self, 'vfs-list-directory',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.directory.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=database_subnets,
            security_groups=[database.sg]
        )
        vfs_list_path.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(vfs_id_list_lambda),
            method_responses=method_responses,
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
        vfs_mkdir_path = vfs_id_mkdir.add_resource("{filepath+}")

        vfs_id_mkdir_lambda = _lambda.Function(
            self, 'vfs-mkdir-directory',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.mkdir.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30),
            vpc=database.vpc,
            vpc_subnets=database_subnets,
            security_groups=[database.sg]
        )
        vfs_mkdir_path.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_id_mkdir_lambda),
            method_responses=method_responses,
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
            vpc_subnets=database_subnets,
            security_groups=[database.sg]
        )
        vfs_id_share.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(vfs_id_share_lambda),
            method_responses=method_responses,
            authorizer = key_authorizer,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
        )
        database.grant_access(vfs_id_share_lambda)
        

        

        