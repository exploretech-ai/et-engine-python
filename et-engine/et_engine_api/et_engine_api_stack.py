from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as certificatemanager,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_ecs as ecs
)
import aws_cdk as cdk
from constructs import Construct


class MasterDB(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self, 
            "RDSVPC",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="privatelambda",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ), 
                ec2.SubnetConfiguration(
                    name="public",
                    cidr_mask=24,
                    subnet_type=ec2.SubnetType.PUBLIC
                )
            ]
        ) 
        
        db_security_group = ec2.SecurityGroup(
            self,
            'DBSecurityGroup',
            vpc=vpc
        )
        lambda_security_group = ec2.SecurityGroup(
            self,
            'RDSLambdaSecurityGroup',
            vpc=vpc
        )
        db_security_group.add_ingress_rule(
            lambda_security_group,
            ec2.Port.tcp(5432),
            'Lambda to Postgres database'
        )
        
        db_secret = rds.DatabaseSecret(
            self,
            "RDSSecret",
            username="postgres"
        )

        
        database = rds.DatabaseInstance(self, "PostgresInstance",
            engine=rds.DatabaseInstanceEngine.POSTGRES,
            database_name="EngineMasterDB",
            credentials=rds.Credentials.from_secret(db_secret),
            vpc=vpc,
            security_groups=[db_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnets=vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            # storage_encrypted=True # <--- eventually need to do this
        )

        
        lambda_function = _lambda.Function(
            self, "DatabaseInitFunction",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="rds_init.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "DB_HOST": database.db_instance_endpoint_address,
                "DB_PORT": database.db_instance_endpoint_port,
                "DB_NAME": database.instance_resource_id,
                "SECRET_ARN": db_secret.secret_arn
            },
            timeout=cdk.Duration.minutes(5),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[lambda_security_group]
        )

        
        database.grant_connect(lambda_function)
        db_secret.grant_read(lambda_function)


        self.database = database
        self.db_secret = db_secret
        self.vpc = vpc
        self.sg = lambda_security_group


    def grant_access(self, lambda_function, access = None):        
        self.db_secret.grant_read(lambda_function)
        self.database.grant_connect(lambda_function)


class API(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
        template_bucket = s3.Bucket(self, "Templates", bucket_name="et-engine-templates")
        tools_update_lambda = _lambda.Function(
            self, 'tool-template-update',
            description="Script to update computing templates",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.update.handler",
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
        database.grant_access(tools_update_lambda)
        tools_update_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:UpdateStack',
                    'ssm:GetParameters',
                    's3:*',
                    'ec2:*',
                    'iam:*',
                    'ecr:CreateRepository',
                    'ecr:DeleteRepository',
                    'ecr:DescribeRepositories',
                    'ecs:CreateCluster',
                    'ecs:DeleteCluster',
                    'ecs:DescribeClusters',
                    'ecs:RegisterTaskDefinition',
                    'ecs:DeregisterTaskDefinition',
                    'ecs:DescribeTaskDefinition',
                    'iam:PutRolePolicy',
                    'iam:GetRolePolicy',
                    'iam:DeleteRolePolicy',
                    'iam:AttachRolePolicy',
                    'iam:DetachRolePolicy',
                    'iam:CreateRole',
                    'iam:DeleteRole',
                    'iam:GetRole',
                    'iam:PassRole',
                    'logs:DeleteLogGroup',
                    'codebuild:CreateProject',
                    'codebuild:DeleteProject',
                    'codebuild:UpdateProject',
                    'lambda:CreateFunction',
                    'lambda:DeleteFunction',
                    'lambda:GetFunction',
                    'lambda:AddPermission',
                    'lambda:RemovePermission',
                    'lambda:InvokeFunction',
                    'lambda:UpdateFunctionCode',
                ],
                resources=['*']
            )
        )

        template_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, 
            s3n.LambdaDestination(tools_update_lambda)
        )

        # COMPUTE CLUSTER CONFIG
        self.vpc = ec2.CfnVPC(
            self,
            "ClusterVPC",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            cidr_block="10.0.0.0/16"
        )
        self.public_subnet = ec2.CfnSubnet(
            self,
            "PublicSubnet",
            vpc_id=self.vpc.attr_vpc_id,
            availability_zone="us-east-2a",
            cidr_block="10.0.0.0/18",
            map_public_ip_on_launch=True
        )
        internet_gateway = ec2.CfnInternetGateway(
            self, 
            "InternetGateway"
        )
        gateway_attachment = ec2.CfnVPCGatewayAttachment(
            self,
            "GatewayAttachment",
            vpc_id=self.vpc.attr_vpc_id,
            internet_gateway_id=internet_gateway.attr_internet_gateway_id
        )
        public_route_table = ec2.CfnRouteTable(
            self,
            "PublicRouteTable",
            vpc_id=self.vpc.attr_vpc_id
        )
        public_route = ec2.CfnRoute(
            self,
            "PublicRoute",
            route_table_id=public_route_table.attr_route_table_id,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        public_subnet_route_table_association = ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnetRouteTableAssociation",
            subnet_id=self.public_subnet.attr_subnet_id,
            route_table_id=public_route_table.attr_route_table_id
        )
        self.security_group = ec2.CfnSecurityGroup(
            self,
            "SecurityGroup",
            group_description="Security group for ECS Cluster",
            vpc_id=self.vpc.attr_vpc_id
        )
        self.ecs_cluster = ecs.CfnCluster(
            self,
            "ECSCluster"
        )


        # USER POOL
        self.user_pool = cognito.UserPool(
            self, 
            "UserPool",
            user_pool_name="APIPool",
            self_sign_up_enabled=True,
            sign_in_aliases={
                'email': True,
                'username': False
            },
            standard_attributes={
                'email': {
                    'required': True,
                    'mutable': True
                }
            }
        )
        self.api_client = self.user_pool.add_client(
            "APIClient",
            auth_flows = cognito.AuthFlow(user_password = True)
        )
        self.webapp_client = self.user_pool.add_client(
            "WebappClient"
        )


        # API DEFNITION
        self.api = apigateway.RestApi(
            self, 'API',
            rest_api_name='ETEngineAPI',
            description='Core API for provisioning resources and running workflows',
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            'CognitoAuthorizer',
            cognito_user_pools=[self.user_pool]
        )

        key_authorizer_lambda = _lambda.Function(
            self, 'key-authorizer-lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "key-authorizer.handler",
            code=_lambda.Code.from_asset('lambda'),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        database.grant_access(key_authorizer_lambda)
        key_authorizer = apigateway.TokenAuthorizer(
            self,
            'key-authorizer',
            handler=key_authorizer_lambda
        )


        # API KEY METHODS
        keys = self.api.root.add_resource("keys")
        keys_create_lambda = _lambda.Function(
            self, 'keys-create-lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "keys.create.handler",
            code=_lambda.Code.from_asset('lambda'),
            timeout = Duration.seconds(30),
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
        # keys_delete_lambda

        # VFS API METHODS
        vfs = self.api.root.add_resource("vfs")
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
                    's3:CreateBucket'
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
                    's3:ListBucket',
                    's3:DeleteObject',
                    's3:DeleteBucket'
                ],
                resources=['*']
            )
        )


        vfs_id = vfs.add_resource("{vfsID}")
        vfs_upload_lambda = _lambda.Function(
            self, 'vfs-upload',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.upload.handler",
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
                    's3:PutObject'
                ],
                resources=['*']
            )
        )
        
        vfs_download_lambda = _lambda.Function(
            self, 'vfs-download',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.download.handler",
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
                    's3:GetObject'
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
                    's3:ListBucket'
                ],
                resources=['*']
            )
        )


        # TOOLS API METHODS
        tools = self.api.root.add_resource("tools")
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
                    'ecs:CreateCluster',
                    'ecs:DeleteCluster',
                    'ecs:DescribeClusters',
                    'ecs:RegisterTaskDefinition',
                    'ecs:DeregisterTaskDefinition',
                    'ecs:DescribeTaskDefinition',
                    'iam:PutRolePolicy',
                    'iam:GetRolePolicy',
                    'iam:DeleteRolePolicy',
                    'iam:AttachRolePolicy',
                    'iam:DetachRolePolicy',
                    'iam:CreateRole',
                    'iam:DeleteRole',
                    'iam:GetRole',
                    'iam:PassRole',
                    'logs:DeleteLogGroup',
                    'codebuild:CreateProject',
                    'codebuild:DeleteProject',
                    'lambda:CreateFunction',
                    'lambda:DeleteFunction',
                    'lambda:GetFunction',
                    'lambda:AddPermission',
                    'lambda:RemovePermission',
                    'lambda:InvokeFunction'
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
                    'ecs:DeregisterTaskDefinition',
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
                    'iam:PassRole'
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
        

        tools_code = tools_id.add_resource('code')
        tools_code_get_lambda = _lambda.Function(
            self, 'tools-code-get',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.code.get.handler",
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
        tools_code.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(tools_code_get_lambda),
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
        database.grant_access(tools_code_get_lambda)
        tools_code_get_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:ListBucket'
                ],
                resources=['*']
            )
        )

        tools_build = tools_id.add_resource('build')
        tools_build_get_lambda = _lambda.Function(
            self, 'tools-build-get',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.build.get.handler",
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
        tools_build.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(tools_build_get_lambda),
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
        database.grant_access(tools_build_get_lambda)
        tools_build_get_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'codebuild:ListBuildsForProject',
                    'codebuild:BatchGetBuilds'
                ],
                resources=['*']
            )
        )

        tools_tasks = tools_id.add_resource('tasks')
        tools_tasks_get_lambda = _lambda.Function(
            self, 'tools-tasks-get',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "tools.tasks.get.handler",
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
        tools_tasks.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(tools_tasks_get_lambda),
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
        database.grant_access(tools_tasks_get_lambda)
        tools_tasks_get_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'ecr:DescribeImages'
                ],
                resources=['*']
            )
        )
        
        
        # POST + body = execute tool with params in body
        # GET = fetch tool description


class WebApp(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        bucket = s3.Bucket(
            self, 
            'webapp-bucket',
            website_index_document='index.html',
            # website_error_document="error.html",
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            access_control = s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL
        )
        # iam_role = iam.Role(
        #     self, 
        #     'engine-webapp-role',
        #     assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        # )
        bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect = iam.Effect.ALLOW,
                actions = ['s3:GetObject'],
                resources = [f"{bucket.bucket_arn}/*"],
                principals = [iam.AnyPrincipal()]
            )
        )

        # source_code = s3_deploy.Source.asset(path='./webapp')
        # self.bucket_deploy = s3_deploy.BucketDeployment(
        #     self, 
        #     'webapp-bucket-deploy', 
        #     sources=[source_code],
        #     destination_bucket=bucket
        # )
        
        # self.handler = _lambda.Function(
        #     self,
        #     "WebAppHandler",
        #     runtime=_lambda.Runtime.NODEJS_14_X,
        #     handler= "app",
        #     code=_lambda.Code.from_bucket(
        #         self.bucket, 
        #         "app.app.handler"
        #     ), 
        #     timeout = Duration.seconds(10))

        hosted_zone = route53.HostedZone.from_lookup(
            self, 
            'exploretech-ai', 
            domain_name='exploretech.ai'
        )
        
        # certificate = certificatemanager.Certificate(self, "webapp-certificate",
        #     domain_name="engine.exploretech.ai",
        #     certificate_name="Hello World Service",  # Optionally provide an certificate name
        #     validation=certificatemanager.CertificateValidation.from_dns(hosted_zone)
        # )

        cloudfront_distribution = cloudfront.Distribution(self, 'WebsiteDistribution',
            default_behavior=cloudfront.BehaviorOptions(origin=origins.S3Origin(bucket)),
            domain_names=['engine.exploretech.ai'],
            certificate=certificatemanager.Certificate.from_certificate_arn(
                self,
                id="54682f3a-faa2-4b82-a79b-0c598baa6724",
                certificate_arn='arn:aws:acm:us-east-1:734818840861:certificate/54682f3a-faa2-4b82-a79b-0c598baa6724'
            )
        )
        route53.ARecord(self, 'WebsiteAliasRecord',
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(cloudfront_distribution)),
            record_name='engine',  # Replace with your subdomain
        )

        CfnOutput(
            self,
            'WebAppBucket',
            value = bucket.bucket_name
        )

      
class ETEngine(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        database = MasterDB(self, "MasterDB")
        # compute = Compute(self, "Compute", database)
        api = API(self, "API", database)
        webapp = WebApp(self, 'WebApp', env = cdk.Environment(account="734818840861", region="us-east-2"))
        

        CfnOutput(
            self,
            "APIURL",
            value = api.api.url
        )
        CfnOutput(
            self,
            "UserPoolID",
            value=api.user_pool.user_pool_id
        )
        CfnOutput(
            self,
            "APIClientID",
            value=api.api_client.user_pool_client_id
        )
        CfnOutput(
            self,
            "WebAppClientID",
            value=api.webapp_client.user_pool_client_id
        )

        CfnOutput(
            self,
            "ComputeClusterVPCID",
            value=api.vpc.attr_vpc_id
        )
        CfnOutput(
            self,
            "ClusterName",
            value=api.ecs_cluster.attr_arn
        )
        CfnOutput(
            self,
            "SecurityGroupID",
            value=api.security_group.attr_group_id
        )
        CfnOutput(
            self,
            "PublicSubnetId",
            value=api.public_subnet.attr_subnet_id
        )

