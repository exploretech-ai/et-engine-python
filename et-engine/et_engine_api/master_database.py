from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_rds as rds,
    aws_ec2 as ec2
)
import aws_cdk as cdk
from constructs import Construct


class MasterDB(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
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
            vpc=self.vpc
        )
        
        lambda_security_group = ec2.SecurityGroup(
            self,
            'RDSLambdaSecurityGroup',
            vpc=self.vpc
        )       
        self.fargate_service_security_group = ec2.SecurityGroup(
            # For ECS web server
            self, 
            "LoadBalancerSecurityGroup", 
            vpc=self.vpc
        )

        db_security_group.add_ingress_rule(
            lambda_security_group,
            ec2.Port.tcp(5432),
            'Lambda to Postgres database'
        )
        db_security_group.add_ingress_rule(
            self.fargate_service_security_group,
            ec2.Port.tcp(5432),
            'Fargate Service to Postgres database'
        )
        self.fargate_service_security_group.add_ingress_rule(
            ec2.Port.tcp(80),
            ec2.Peer.any_ipv4(),
            'Load balancer to fargate service'
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
            vpc=self.vpc,
            security_groups=[db_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnets=self.vpc.select_subnets(
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
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=self.vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnets
            ),
            security_groups=[lambda_security_group]
        )

        
        database.grant_connect(lambda_function)
        db_secret.grant_read(lambda_function)


        self.database = database
        self.db_secret = db_secret
        self.vpc = self.vpc
        self.sg = lambda_security_group


    def grant_access(self, lambda_function):        
        self.db_secret.grant_read(lambda_function)
        self.database.grant_connect(lambda_function)
