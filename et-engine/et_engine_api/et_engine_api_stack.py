from aws_cdk import (
    Stack,
    CfnOutput,
)
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
        data_transfer_utils = DataTransfer(self, f"DataTransfer{env}", compute, api)
        
        # Compute cluster outputs
        # CfnOutput(self, "ComputeClusterVpcID", value=compute.vpc.vpc_id)
        # CfnOutput(self, "ClusterName", value=compute.ecs_cluster.cluster_name)
        # CfnOutput(self, "TaskExecutionRoleArn", value=compute.task_role.role_arn)

        # User Pool outputs
        CfnOutput(self, "UserPoolID", value=user_pool.user_pool.user_pool_id)
        CfnOutput(self, "APIClientID", value=user_pool.api_client.user_pool_client_id)
        CfnOutput(self, "WebAppClientID", value=user_pool.webapp_client.user_pool_client_id)
        
        # Data Transfer outputs
        # CfnOutput(self, "UploadContainerUri", value=data_transfer_utils.upload_image.image_uri)
        # CfnOutput(self, "UploadRoleArn", value=data_transfer_utils.data_upload_task_role.role_arn)
        # CfnOutput(self, "DownloadS3ToEfsFunctionArn", value=data_transfer_utils.launch_download_from_s3_to_efs.function_arn)
        


        


