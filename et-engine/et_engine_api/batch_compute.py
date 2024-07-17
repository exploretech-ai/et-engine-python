from aws_cdk import (
    Stack,
    Size,
    aws_batch as batch,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_sqs as sqs
)
from constructs import Construct


class BatchCompute(Stack):
    def __init__(self, scope: Construct, construct_id: str, network, compute, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        compute_environment = batch.ManagedEc2EcsComputeEnvironment(self, "Ec2ComputeEnv",
            vpc=network.vpc
        )
        queue = batch.JobQueue(self, "JobQueue",
            compute_environments=[batch.OrderedComputeEnvironment(
                compute_environment=compute_environment,
                order=1
            )],
            priority=10
        )

        self.job_role = iam.Role(
            self,
            "ECSTaskRole",
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )
        self.job_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'ecr:*',
                    'elasticfilesystem:*',
                    "sts:*",
                    "logs:*"
                ],
                resources=['*']
            )
        )

        # Job Submission Queue
        self.job_submitter_queue = sqs.Queue(self, "JobSubmitterQueue",
            fifo=True
        )
        job_submitter_image = ecr_assets.DockerImageAsset(self, "JobSubmitterImage", 
            directory="docker/job_submitter",
            platform=ecr_assets.Platform.LINUX_AMD64
        )   
        job_submitter_task = ecs.FargateTaskDefinition(self, "JobSubmitterTaskDefinition")
        job_submitter_task.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    'logs:*',
                    'cloudformation:*',
                    'ecr:*',
                    'ssm:*',
                    'ecs:*',
                    'iam:*',
                    'batch:*'
                ],
                resources=['*']
            )
        )
        job_submitter_task.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=[
                    'sqs:*'
                ],
                resources=[self.job_submitter_queue.queue_arn]
            )
        )
        job_submitter_container = job_submitter_task.add_container("JobSubmitterContainer",
            image = ecs.ContainerImage.from_docker_image_asset(job_submitter_image),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="JobSubmitterContainer",
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                max_buffer_size=Size.mebibytes(25)
            ),          
            environment={
                'JOB_SUBMISSION_QUEUE_URL': self.job_submitter_queue.queue_url
            }                          
        )
        job_submitter_fargate_service = ecs.FargateService(self, "JobSubmitterFargateService",
            cluster=compute.ecs_cluster,
            task_definition=job_submitter_task,
            capacity_provider_strategies=[
                compute.fargate_spot_capacity_provider,
                compute.fargate_capacity_provider
            ]
        )       
        

        