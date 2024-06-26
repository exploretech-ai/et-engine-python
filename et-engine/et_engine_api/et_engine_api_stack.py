from aws_cdk import (
    Stack,
    CfnOutput
)
from constructs import Construct

from .master_database import MasterDB
from .rest_api import API
from .templates import Templates
from .compute_cluster import ComputeCluster
from .user_pool import UserPool


class ETEngine(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        database = MasterDB(self, "MasterDB")
        templates = Templates(self, "Templates", database)
        compute = ComputeCluster(self, "ComputeCluster")
        user_pool = UserPool(self, "UserPool")
        api = API(self, "API", database, user_pool.user_pool)      

        CfnOutput(self, "APIURL", value = api.api.url)
        CfnOutput(self, "UserPoolID", value=user_pool.user_pool.user_pool_id)
        CfnOutput(self, "APIClientID", value=user_pool.api_client.user_pool_client_id)
        CfnOutput(self, "WebAppClientID", value=user_pool.webapp_client.user_pool_client_id)
        CfnOutput(self, "ComputeClusterVpcID", value=compute.vpc.vpc_id)
        CfnOutput(self, "ClusterName", value=compute.ecs_cluster.cluster_name)
        CfnOutput(self, "TaskExecutionRoleArn", value=compute.task_role.role_arn)


