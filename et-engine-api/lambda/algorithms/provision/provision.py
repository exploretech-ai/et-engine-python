import json
import boto3


def ConfigStorage():

    # Create Bucket
    bucket_stack = {
        "Type": "AWS::S3::Bucket"
    }
    
    return bucket_stack

def ConfigCompute(algo_ID):
    """
    ECS VPC configuration from here: https://containersonaws.com/pattern/low-cost-vpc-amazon-ecs-cluster
    
    """

    # PROVISIONING GOES HERE
    # 1. New ECR Repository
    RepositoryName = f"engine-ecr-0-{algo_ID}"
    compute_stack = {}
    
    compute_stack['VPC'] = {
        "Type": "AWS::EC2::VPC",
        "Properties": {
            "EnableDnsSupport": True,
            "EnableDnsHostnames": True,
            "CidrBlock": {
                "Fn::FindInMap": [
                    "SubnetConfig",
                    "VPC",
                    "CIDR"
                ]
            }
        }
    }
    compute_stack['PublicSubnetOne'] = {
        "Type": "AWS::EC2::Subnet",
        "Properties": {
            "AvailabilityZone": {
                "Fn::Select": [
                    0,
                    {
                        "Fn::GetAZs": {
                            "Ref": "AWS::Region"
                        }
                    }
                ]
            },
            "VpcId": {
                "Ref": "VPC"
            },
            "CidrBlock": {
                "Fn::FindInMap": [
                    "SubnetConfig",
                    "PublicOne",
                    "CIDR"
                ]
            },
            "MapPublicIpOnLaunch": True
        }
    }
    compute_stack["InternetGateway"] = {
        "Type": "AWS::EC2::InternetGateway"
    }
    compute_stack["GatewayAttachement"] = {
        "Type": "AWS::EC2::VPCGatewayAttachment",
        "Properties": {
            "VpcId": {
                "Ref": "VPC"
            },
            "InternetGatewayId": {
                "Ref": "InternetGateway"
            }
        }
    }
    compute_stack["PublicRouteTable"] = {
        "Type": "AWS::EC2::RouteTable",
        "Properties": {
            "VpcId": {
                "Ref": "VPC"
            }
        }
    }
    compute_stack["PublicRoute"] = {
        "Type": "AWS::EC2::Route",
        "DependsOn": "GatewayAttachement",
        "Properties": {
            "RouteTableId": {
                "Ref": "PublicRouteTable"
            },
            "DestinationCidrBlock": "0.0.0.0/0",
            "GatewayId": {
                "Ref": "InternetGateway"
            }
        }
    }
    compute_stack["PublicSubnetOneRouteTableAssociation"] = {
        "Type": "AWS::EC2::SubnetRouteTableAssociation",
        "Properties": {
            "SubnetId": {
                "Ref": "PublicSubnetOne"
            },
            "RouteTableId": {
                "Ref": "PublicRouteTable"
            }
        }
    }


    compute_stack["SecurityGroup"] = {
        "Type" : "AWS::EC2::SecurityGroup",
        "Properties" : {
            "GroupDescription" : f"Security group for ECS Cluster",
            "VpcId" : {
                "Ref" : "VPC"
            }
        }
    }
    compute_stack['ContainerRepo'] = {
        "Type": "AWS::ECR::Repository",
        "Properties": {
            "RepositoryName": RepositoryName
        }
    }
    compute_stack['ECSCluster'] = {
        "Type": "AWS::ECS::Cluster"
    }
    compute_stack['ECSTaskDefinition'] = {
        "Type": "AWS::ECS::TaskDefinition",
        "Properties": {
            "Cpu": 256,
            "Memory": 512,
            "NetworkMode": "awsvpc",
            "RequiresCompatibilities": [
                "FARGATE"
            ],
            "ExecutionRoleArn": {
                "Fn::GetAtt": [
                    "ECSTaskExecutionRole",
                    "Arn"
                ]
            },
            "ContainerDefinitions": [
                {
                    "Name": "hello-world-container",
                    "Image": {
                        "Fn::Sub": ["${repo}:latest", {
                            "repo": {
                                "Fn::GetAtt" : [
                                    "ContainerRepo",
                                    "RepositoryUri"
                                ]
                            }
                        }]
                    },
                    "Essential": True,
                    "LogConfiguration": {
                        "LogDriver": "awslogs",
                        "Options": {
                            "awslogs-group": {
                                "Ref": "ECSLogGroup"
                            },
                            "awslogs-region": {
                                "Ref": "AWS::Region"
                            },
                            "awslogs-stream-prefix": f"{algo_ID}"
                        }
                    }
                }
            ]
        }
    }
    compute_stack['ECSTaskExecutionRole'] = {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ecs-tasks.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            "Policies": [
                {
                    "PolicyName": "ECSTaskExecutionPolicy",
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents",
                                    "ecr:*"
                                ],
                                "Resource": "*"
                            }
                        ]
                    }
                }
            ]
        }
    }   
    compute_stack['ECSLogGroup'] = {
        "Type": "AWS::Logs::LogGroup",
        "Properties": {
            "LogGroupName": f"/ecs/hello-world-task-{algo_ID}"
        }
    }
    compute_stack["CodeBuildRole"] = {
        "Type": "AWS::IAM::Role",
        "Properties": {
            "RoleName": {
                "Fn::Sub": "CodeBuildRole-${AWS::StackName}"
            },
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "codebuild.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            "Policies": [
                {
                    "PolicyName": "CodeBuildPolicy",
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "ecr:*"
                                ],
                                "Resource": {
                                    "Fn::GetAtt": [
                                        "ContainerRepo",
                                        "Arn"
                                    ]
                                }
                            },
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "logs:CreateLogStream",
                                    "logs:CreateLogGroup",
                                    "logs:PutLogEvents",
                                    "ecr:GetAuthorizationToken"
                                ],
                                "Resource": "*"
                            },
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "s3:Get*",
                                    "s3:List*"
                                ],
                                "Resource": [
                                    {
                                        "Fn::GetAtt": [
                                            "CodeBuildBucket",
                                            "Arn"
                                        ]
                                    },
                                    {
                                        "Fn::Sub": ["${CBBucket}/*", {
                                            "CBBucket": {
                                                "Fn::GetAtt" : [
                                                    "CodeBuildBucket",
                                                    "Arn"
                                                ]
                                            }
                                        }]
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }  
    repo_location = {
        "Fn::Sub": ["${CurrentFileSystemName}/.engine/", {
            "CurrentFileSystemName": {
                "Ref" : "CodeBuildBucket"
            }
        }]
    }
    compute_stack["CodeBuildBucket"] = {
        "Type": "AWS::S3::Bucket"
    }
    compute_stack["DockerBuilder"] = {
        "Type": "AWS::CodeBuild::Project",
        "Properties": {
            "Source": {
                "Type": "S3",
                "Location": repo_location,
                "BuildSpec": "buildspec.yml"
            },
            "Artifacts" : {
                "Type": "S3",
                "Location": {
                    "Ref" : "CodeBuildBucket"
                }
            },
            "Environment": {
                "Type": "LINUX_CONTAINER",
                "ComputeType": "BUILD_GENERAL1_SMALL",
                "Image": "aws/codebuild/standard:4.0",
                "PrivilegedMode": True,
                "EnvironmentVariables": [
                    {
                        "Name": "IMAGE_TAG",
                        "Value": "latest"
                    },
                    {
                        "Name": "AWS_DEFAULT_REGION",
                        "Value": {
                            "Ref": "AWS::Region"
                        }
                    },
                    {
                        "Name": "ECR_REPO_URI",
                        "Value": {
                            "Fn::GetAtt": [
                                "ContainerRepo",
                                "RepositoryUri"
                            ]
                        }
                    },
                    {
                        "Name": "IMAGE_REPO_NAME",
                        "Value": {
                            "Ref": "ContainerRepo"
                        }
                    },
                    {
                        "Name": "AWS_ACCOUNT_ID",
                        "Value": {
                            "Ref": "AWS::AccountId"
                        }
                    }
                ]
            },
            "ServiceRole": {
                "Fn::GetAtt": [
                    "CodeBuildRole",
                    "Arn"
                ]
            }
        }
    }


    return compute_stack

def ProvisionResources(algo_ID):
    # Check if config gives you the keys: 'storage' and 'compute'

    compute_stack = ConfigCompute(algo_ID)

    template = {
        'Resources': compute_stack
    }
    template['Mappings'] = {
        "SubnetConfig": {
            "VPC": {
                "CIDR": "10.0.0.0/16"
            },
            "PublicOne": {
                "CIDR": "10.0.0.0/18"
            }
        }
    }
    template['Resources']['FileSystem'] = {
        "Type": "AWS::S3::Bucket"
    }
    template['Outputs'] = {
        "ClusterName" : {
            "Description" : "Name of ECS Cluster for running tasks",
            "Value" : {
                "Ref": "ECSCluster"
            }
        },
        "TaskName" : {
            "Description" : "Name of the ECS task to be run",
            "Value" : {
                "Ref" :  "ECSTaskDefinition"
            }
        },
        "SecurityGroupID" : {
            "Description" : "Security group for custom VPC",
            "Value" : {
                "Ref" : "SecurityGroup"
            }
        },
        "FileSystemName" : {
            "Description" : "User File System s3 Bucket Name",
            "Value" : {
                "Ref" : "FileSystem"
            }
        },
        "CodeBuildBucketName": {
            "Description" : "s3 bucket for holding code build info",
            "Value": {
                "Ref": "CodeBuildBucket"
            }
        },
        "DockerBuilderName" : {
            "Description": "name of the CodeBuild project that builds the dockerfile",
            "Value" : {
                "Ref" : "DockerBuilder"
            }
        },
        "ContainerRepoName" : {
            "Description" : "name of the ECR repo",
            "Value" : {
                "Ref" : "ContainerRepo"
            }
        },
        "VpcId": {
            "Description": "The ID of the VPC that this stack is deployed in",
            "Value": {
                "Ref": "VPC"
            }
        },
        "PublicSubnetId": {
            "Description": "public facing subnets that have a direct internet connection as long as you assign a public IP (for ECS)",
            "Value": {
                "Fn::Sub": "${PublicSubnetOne}"
            }
        }
    }

    return template


def handler(event, context):

    try:
        algoID = event['pathParameters']['algoID']
        stack = ProvisionResources(algoID)

        cf = boto3.client('cloudformation')
        cf.create_stack(
            StackName = f"engine-algo-{algoID}", 
            TemplateBody = json.dumps(stack),
            OnFailure = 'DELETE',
            Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
        )

        return {
            'statusCode': 200,
            'body': json.dumps("This request will provision the provided algoID")
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {e}")
        }


    

