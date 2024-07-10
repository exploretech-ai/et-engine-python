from aws_cdk import (
    Stack,
    aws_ec2 as ec2
)
from constructs import Construct

class Network(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.vpc = ec2.Vpc(
            self, 
            "EngineVPC",
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
        
        # For the Master Database
        self.database_security_group = ec2.SecurityGroup(
            self,
            'DBSecurityGroup',
            vpc=self.vpc
        )

        # For lambda functions that need access to the database
        self.database_lambda_security_group = ec2.SecurityGroup(
            self,
            'RDSLambdaSecurityGroup',
            vpc=self.vpc
        )      
        self.database_security_group.add_ingress_rule(
            self.database_lambda_security_group,
            ec2.Port.tcp(5432),
            'Lambda to Postgres database'
        ) 
        
        # For the fargate-based web server
        self.fargate_service_security_group = ec2.SecurityGroup(
            self, 
            "LoadBalancerSecurityGroup", 
            vpc=self.vpc
        )
        self.fargate_service_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            'Load balancer to fargate service'
        )
        self.database_security_group.add_ingress_rule(
            self.fargate_service_security_group,
            ec2.Port.tcp(5432),
            'Fargate Service to Postgres database'
        )

        # Security group for connecting EFS filesystems to tasks on ECS
        self.efs_security_group = ec2.SecurityGroup(
            self,
            "EfsSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound = True,
        )
        self.efs_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(2049)
        )
        
        