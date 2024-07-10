from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_iam as iam
)
import aws_cdk as cdk
from constructs import Construct


class MasterDatabase(Stack):
    def __init__(self, scope: Construct, construct_id: str, network, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.database_name = "EngineMasterDatabase"


        self.database_secret = rds.DatabaseSecret(
            self,
            "RDSSecret",
            username="postgres"
        )

        
        self.database = rds.DatabaseInstance(self, "EncryptedPostgresInstance",
            engine=rds.DatabaseInstanceEngine.POSTGRES,
            database_name=self.database_name,
            credentials=rds.Credentials.from_secret(self.database_secret),
            vpc=network.vpc,
            security_groups=[network.database_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnets=network.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            storage_encrypted=True 
        )

        
        lambda_function = _lambda.Function(
            self, "DatabaseInitFunction",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="rds_init.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "DB_HOST": self.database.db_instance_endpoint_address,
                "DB_PORT": self.database.db_instance_endpoint_port,
                "DB_NAME": self.database.instance_resource_id,
                "SECRET_ARN": self.database_secret.secret_arn,
                "DATABASE_SHORT_NAME": self.database_name,
                "SECRET_NAME": self.database_secret.secret_name
            },
            timeout=cdk.Duration.minutes(5),
            vpc=network.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=network.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[network.database_lambda_security_group]
        )
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue',
                ],
                resources=[
                    self.database_secret.secret_arn
                ]
            )
        )

        
        self.database.grant_connect(lambda_function)
        self.database_secret.grant_read(lambda_function)

    def grant_access(self, lambda_function):        
        self.database_secret.grant_read(lambda_function)
        self.database.grant_connect(lambda_function)