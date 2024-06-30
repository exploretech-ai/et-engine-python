from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigateway
)
from constructs import Construct


class DataTransfer(Stack):
    def __init__(self, scope: Construct, construct_id: str, api, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Temporary s3 bucket
        transfer_bucket = s3.Bucket(
            self,
            "TransferBucket",
            auto_delete_objects = True,
            removal_policy=RemovalPolicy.DESTROY,
            bucket_name = "temp-data-transfer-bucket-test"
        )
        transfer_bucket.add_cors_rule(
            allowed_origins=["*"],
            allowed_methods=[
                s3.HttpMethods.PUT,
                s3.HttpMethods.POST,
                s3.HttpMethods.GET,
                s3.HttpMethods.DELETE,
                s3.HttpMethods.HEAD,
            ],
            allowed_headers=["*"],
            max_age=3000,
        )

        # Temporary API resource with POST/GET

        tmp_resource = api.api.root.add_resource("tmp")

        vfs_upload_lambda = _lambda.Function(
            self, 'vfs-upload-tmp',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.temp_upload.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.minutes(5)
        )
        vfs_upload_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*'
                ],
                resources=[
                    transfer_bucket.bucket_arn,
                    transfer_bucket.bucket_arn + "/*"
                ]
            )
        )
        tmp_resource.add_method(
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
            authorizer = api.key_authorizer,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
        )

        vfs_download_lambda = _lambda.Function(
            self, 'vfs-download',
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler= "vfs.temp_download.handler",
            code=_lambda.Code.from_asset('lambda'),  # Assuming your Lambda code is in a folder named 'lambda'
            timeout = Duration.seconds(30)
        )
        tmp_resource.add_method(
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
            authorizer = api.key_authorizer,
            authorization_type = apigateway.AuthorizationType.CUSTOM,
        )
        vfs_download_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    's3:*'
                ],
                resources=[
                    transfer_bucket.bucket_arn,
                    transfer_bucket.bucket_arn + "/*"
                ]
            )
        )

        CfnOutput(self, "TransferBucketName", value=transfer_bucket.bucket_name)
        