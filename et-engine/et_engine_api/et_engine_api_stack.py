from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_s3 as s3,
    aws_apigateway as apigateway,
    aws_s3_deployment as s3_deploy,
    aws_lambda as _lambda,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as certificatemanager,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_iam as iam,
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
            )
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

        # Create an API Gateway
        self.api = apigateway.RestApi(
            self, 'API',
            rest_api_name='ETEngineAPI',
            description='Core API for provisioning resources and running workflows',
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )


        users = self.api.root.add_resource("users")
        users_create_lambda = _lambda.Function(
            self, 'users-create',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "users.create.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            # timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        users.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(users_create_lambda),
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
        database.grant_access(users_create_lambda)
        users_create_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:DescribeStacks'
                ],
                resources=["*"]
            )
        )

        users_list_lambda = _lambda.Function(
            self, 'users-list',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "users.list.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            # timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        users.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(users_list_lambda),
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
        database.grant_access(users_list_lambda)


        user_id = users.add_resource("{userID}")   
        user_id_describe_lambda = _lambda.Function(
            self, 'user-id-describe',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "users.user.describe.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            # timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        user_id.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(user_id_describe_lambda),
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
        database.grant_access(user_id_describe_lambda)

        
        workflows = user_id.add_resource("workflows")
        workflows_create_lambda = _lambda.Function(
            self, 'workflow-create',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.create.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            # timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        workflows.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(workflows_create_lambda),
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
        database.grant_access(workflows_create_lambda)
        
        workflows_list_lambda = _lambda.Function(
            self, 'workflow-list',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.list.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            # timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        workflows.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(workflows_list_lambda),
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
        database.grant_access(workflows_list_lambda)


        workflow_id = workflows.add_resource("{workflowID}")
        workflow_id_describe_lambda = _lambda.Function(
            self, 'workflow-describe',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.describe.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            # timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        workflow_id.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(workflow_id_describe_lambda),
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
        database.grant_access(workflow_id_describe_lambda)


        # workflow_submit = workflow_id.add_resource("submit")
        workflow_id_submit_lambda = _lambda.Function(
            self, 'workflow-submit',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.submit.submit.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        workflow_id.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(workflow_id_submit_lambda),
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
        workflow_id_submit_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*'
                ],
                resources=['*']
            )
        )
        database.grant_access(workflow_id_submit_lambda)

        modules = workflow_id.add_resource("modules")
        modules_list_lambda = _lambda.Function(
            self, 'modules-list',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.modules.list.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            # timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        modules.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(modules_list_lambda),
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


        module_name = modules.add_resource("{moduleName}")
        module_describe_lambda = _lambda.Function(
            self, 'module-describe',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.modules.module.describe.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            # timeout = Duration.minutes(5),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        module_name.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(module_describe_lambda),
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


        module_provision = module_name.add_resource("provision")
        module_provision_lambda = _lambda.Function(
            self, 'workflow-provision',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.modules.module.provision.provision.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg],
            timeout=Duration.seconds(10)
        )
        module_provision.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(module_provision_lambda),
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
        module_provision_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:*',
                    'iam:*',
                    'log-group:*',
                    'logs:*',
                    'ec2:*',
                    'ecr:*',
                    'ecs:*',
                    's3:*',
                    'codebuild:*',
                    'ssm:*'
                ],
                resources=['*']
            )
        )

        module_provision_status_lambda = _lambda.Function(
            self, 'workflow-provision-status',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.modules.module.provision.status.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        module_provision.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(module_provision_status_lambda),
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
        module_provision_status_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions = [
                    'cloudformation:DescribeStacks'
                ],
                resources=["*"]
            )
        )


        # module_build = module_name.add_resource("build")
        # module_build_lambda = _lambda.Function(
        #     self, 'workflow-build',
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler= "workflows.workflow.modules.module.build.build.handler",
        #     code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
        #     vpc=database.vpc,
        #     vpc_subnets=ec2.SubnetSelection(
        #         subnets=database.vpc.select_subnets(
        #             subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        #         ).subnets
        #     ),
        #     security_groups=[database.sg],
        #     timeout=Duration.seconds(30)
        # )
        # module_build.add_method(
        #     "POST",
        #     integration=apigateway.LambdaIntegration(module_build_lambda),
        #     method_responses=[{
        #         'statusCode': '200',
        #         'responseParameters': {
        #             'method.response.header.Content-Type': True,
        #         },
        #         'responseModels': {
        #             'application/json': apigateway.Model.EMPTY_MODEL,
        #         },
        #     }],
        # )
        # module_build_lambda.add_to_role_policy(
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

        # module_build_status_lambda = _lambda.Function(
        #     self, 'workflow-build-status',
        #     runtime=_lambda.Runtime.PYTHON_3_8,
        #     handler= "workflows.workflow.modules.module.build.status.handler",
        #     code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
        #     vpc=database.vpc,
        #     vpc_subnets=ec2.SubnetSelection(
        #         subnets=database.vpc.select_subnets(
        #             subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        #         ).subnets
        #     ),
        #     security_groups=[database.sg]
        # )
        # module_build.add_method(
        #     "GET",
        #     integration=apigateway.LambdaIntegration(module_build_status_lambda),
        #     method_responses=[{
        #         'statusCode': '200',
        #         'responseParameters': {
        #             'method.response.header.Content-Type': True,
        #         },
        #         'responseModels': {
        #             'application/json': apigateway.Model.EMPTY_MODEL,
        #         },
        #     }],
        # )
        

        module_execute = module_name.add_resource("execute")
        module_execute_lambda = _lambda.Function(
            self, 'workflow-execute',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.modules.module.execute.execute.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        module_execute.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(module_execute_lambda),
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
        module_execute_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:DescribeStacks',
                    'ecs:RunTask',
                    'iam:PassRole'
                ],
                resources=["*"]
            )
        )

        module_execute_status_lambda = _lambda.Function(
            self, 'workflow-execute-status',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.modules.module.execute.status.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        module_execute.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(module_execute_status_lambda),
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
        
        
        module_destroy = module_name.add_resource("destroy")
        module_destroy_lambda = _lambda.Function(
            self, 'workflow-destroy',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.modules.module.destroy.destroy.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg],
            timeout=Duration.seconds(30)
        )
        module_destroy.add_method(
            "POST",
            integration=apigateway.LambdaIntegration(module_destroy_lambda),
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
        module_destroy_lambda.add_to_role_policy(
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

        module_destroy_status_lambda = _lambda.Function(
            self, 'workflow-destroy-status',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "workflows.workflow.modules.module.destroy.status.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg]
        )
        module_destroy.add_method(
            "GET",
            integration=apigateway.LambdaIntegration(module_destroy_status_lambda),
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
        

        # workflows_filesystem = workflows_id.add_resource("filesystem")
        # workflows_filesystem.add_method('GET')
        # workflows_filesystem.add_method('POST')

             
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

        self.database = MasterDB(self, "MasterDB")
        self.api = API(self, "API", self.database)
        self.templates = Templates(self, "Templates")
        self.webapp = WebApp(self, 'WebApp', env = cdk.Environment(account="734818840861", region="us-east-2"))

        CfnOutput(
            self,
            "APIURL",
            value = self.api.api.url
        )
        CfnOutput(
            self,
            "TemplateBucket",
            value = self.templates.dockerbuild_template.bucket_name
        )

