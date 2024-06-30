import os

from aws_cdk import (
    Stack,
    CfnOutput,
)
import aws_cdk as cdk
from constructs import Construct

from .master_database import MasterDB
from .rest_api import API
from .templates import Templates
from .compute_cluster import ComputeCluster
from .user_pool import UserPool

from .data_transfer import DataTransfer

class ETEngine(Stack):

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env = config['env']

        database = MasterDB(self, "MasterDB")
        templates = Templates(self, "Templates", database)
        compute = ComputeCluster(self, "ComputeCluster")
        user_pool = UserPool(self, "UserPool")
        api = API(self, f"API{env}", database, user_pool.user_pool, config)      

        CfnOutput(self, "UserPoolID", value=user_pool.user_pool.user_pool_id)
        CfnOutput(self, "APIClientID", value=user_pool.api_client.user_pool_client_id)
        CfnOutput(self, "WebAppClientID", value=user_pool.webapp_client.user_pool_client_id)
        CfnOutput(self, "ComputeClusterVpcID", value=compute.vpc.vpc_id)
        CfnOutput(self, "ClusterName", value=compute.ecs_cluster.cluster_name)
        CfnOutput(self, "TaskExecutionRoleArn", value=compute.task_role.role_arn)

        
        DataTransfer(self, f"DataTransfer{env}", api, env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),)


        # New VFS template stack goes here
        # > Takes a VPC and Security group as params
        # > Lambda function w/ code for interacting with EFS
        # > EFS + access point
        # > Upload bucket
        # >> Download bucket
        # >> HOW TO SYNC EFS WITH DOWNLOAD BUCKET?
        

        # Add testing method to API here
        

        


