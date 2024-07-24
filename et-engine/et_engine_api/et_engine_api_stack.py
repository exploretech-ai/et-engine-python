from aws_cdk import (
    Stack,
    CfnOutput,
)
from constructs import Construct

from .master_database import MasterDatabase
from .templates import Templates
from .compute_cluster import ComputeCluster
from .user_pool import UserPool
from .web_server import WebServer
from .network import Network
from .batch_compute import BatchCompute
from .file_systems import FileSystems


class ETEngine(Stack):

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env = config['env']

        network = Network(self, "Network")
        database = MasterDatabase(self, "MasterDatabase", network)
        user_pool = UserPool(self, "UserPool")
        templates = Templates(self, "Templates", network, database)
        compute = ComputeCluster(self, f"ComputeCluster", network, config)
        batch = BatchCompute(self, f"BatchComputedev", network, compute, database)
        file_systems = FileSystems(self, f"FileSystemsdev", network)
        web_server = WebServer(self, f"ApiWebServer{env}", network, compute, database, batch, file_systems, config)
        
        
        # Network
        CfnOutput(self, "EngineVpcId", value=network.vpc.vpc_id)
        CfnOutput(self, "EfsSecurityGroupId", value=network.efs_security_group.security_group_id)
        CfnOutput(self, "FargateServiceSecurityGroupId", value=network.fargate_service_security_group.security_group_id)

        # User Pool 
        CfnOutput(self, "UserPoolID", value=user_pool.user_pool.user_pool_id)
        CfnOutput(self, "APIClientID", value=user_pool.api_client.user_pool_client_id)
        CfnOutput(self, "WebAppClientID", value=user_pool.webapp_client.user_pool_client_id)

        # Master File System
        CfnOutput(self, "MasterFileSystemArn", value=file_systems.master_file_system.file_system_arn)
        CfnOutput(self, "MasterFileSystemId", value=file_systems.master_file_system.file_system_id)

        # Web Service Compute Cluster
        CfnOutput(self, "ClusterName", value=compute.ecs_cluster.cluster_name)
        CfnOutput(self, "TaskExecutionRoleArn", value=compute.task_role.role_arn)
        CfnOutput(self, "CapacityProviderName", value=compute.capacity_provider.capacity_provider_name)

        # High Performance Computing 
        CfnOutput(self, "JobRole", value=batch.job_role.role_arn)
        

