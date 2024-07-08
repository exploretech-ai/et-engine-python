from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_certificatemanager as ctf,
    aws_route53 as route53,
    aws_route53_targets as r53t,
    aws_iam as iam
)
from constructs import Construct

from .api_methods.api_key_methods import ApiKeyMethods
from .api_methods.vfs_methods import VfsMethods
from .api_methods.tool_methods import ToolMethods
from .api_methods.task_methods import TaskMethods


class API(Stack):
    def __init__(self, scope: Construct, construct_id: str, database, user_pool, compute, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env = config['env']
        subdomain = config['subdomain']

        self.api = apigateway.RestApi(self, 'API',
            rest_api_name=f'ETEngineAPI-{env}',
            description='Core API for provisioning resources and running workflows',
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )

        zone = route53.HostedZone.from_hosted_zone_attributes(self, "zone", 
            hosted_zone_id="Z07247471MNWCOVOV0VX5",
            zone_name="exploretech.ai"
        )
        certificate = ctf.Certificate(self, "apiCert", 
            domain_name=f"{subdomain}.exploretech.ai",
            validation=ctf.CertificateValidation.from_dns(zone)
        )
        
        self.api.add_domain_name("ApiDomain",
            certificate=certificate,
            domain_name=f"{subdomain}.exploretech.ai"
        )
        route53.ARecord(self, "apiDNS",
            zone=zone,
            record_name=subdomain,
            target=route53.RecordTarget.from_alias(r53t.ApiGateway(self.api))
        )

        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            'CognitoAuthorizer',
            cognito_user_pools=[user_pool]
        )

        key_authorizer_lambda = _lambda.Function(
            self, 'key-authorizer-lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "key_authorizer.handler",
            code=_lambda.Code.from_asset('lambda'),
            vpc=database.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=database.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[database.sg],
            timeout = Duration.seconds(30)            
        )
        database.grant_access(key_authorizer_lambda)
        key_authorizer_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue'
                ],
                resources=['arn:aws:secretsmanager:us-east-2:734818840861:secret:api_key_fernet_key-bjdEbo']
            )
        )
        self.key_authorizer = apigateway.TokenAuthorizer(
            self,
            'key-authorizer',
            handler=key_authorizer_lambda,
            results_cache_ttl=Duration.seconds(0)
        )
        

        ApiKeyMethods(self, "ApiKeyMethods", database, self.api, authorizer)
        VfsMethods(self, "VfsMethods", database, self.api, self.key_authorizer, compute)
        ToolMethods(self, "ToolMethods", database, self.api, self.key_authorizer)
        TaskMethods(self, "TaskMethods", database, self.api, self.key_authorizer)

        CfnOutput(self, "ApiUrl", value = self.api.url)