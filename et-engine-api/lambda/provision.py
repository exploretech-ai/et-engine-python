import boto3
import json
from datetime import datetime
import uuid

def ConfigStorage(storage_config, algo_ID):
    if storage_config == 'new':

        # Bucket needs to be specified via: FileSystem-UserID-ResourceID
        bucket_name = f"engine-s3-0-{algo_ID}"

    else:
        raise Exception(f"storage configuration '{storage_config}' not recognized")
        
    # Create Bucket
    bucket_stack = {
        "Type": "AWS::S3::Bucket",
        "Properties": {
            "BucketName": bucket_name
        }
    }
    
    return bucket_stack

def ConfigCompute(compute_config, algo_ID):
    if compute_config == 'SingleNode':
        instance_name = f"engine-cpu-0-{algo_ID}"
    
    else:
        raise Exception(f"instace type '{compute_config}' not recognized")
    
    # PROVISIONING GOES HERE
    # 1. New ECR Repository
    RepositoryName = f"engine-ecr-0-{algo_ID}"
    compute_stack = {}
    compute_stack['VPC'] = {
        "Type": "AWS::EC2::VPC",
        "Properties": {
            "CidrBlock": "10.0.0.0/16",
            "EnableDnsSupport": True,
            "EnableDnsHostnames": True
            # "Tags": [
            #     {
            #         "Key": "Name",
            #         "Value": VPCName
            #     }
            # ]
        }
    }
    compute_stack['Subnet'] = {
        "Type": "AWS::EC2::Subnet",
        "Properties": {
            "VpcId": {
                "Ref": "VPC"
            },
            "CidrBlock": "10.0.0.0/24",
            "AvailabilityZone": "us-east-2a"
            # "Tags": [
            #     {
            #         "Key": "Name"
            #     }
            # ]
            # "Value": SubnetName
        }
    }
    compute_stack["SecurityGroup"] = {
        "Type" : "AWS::EC2::SecurityGroup",
        "Properties" : {
            "GroupDescription" : f"Security group for algorithm {algo_ID}",
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
                        "Fn::Sub": "ubuntu"
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
                                    "logs:PutLogEvents"
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
    # compute_stack['ServiceLinkedRole'] = {
    #     "Type" : "AWS::IAM::ServiceLinkedRole",
    #     "Properties" : {
    #         "AWSServiceName" : "ecs.amazonaws.com",
    #         "Description" : "Link role to ECS"
    #     }
    # }

    # 3. Container Image
    # 4. 

    return compute_stack

def ProvisionResources(config):
    algo_ID = uuid.uuid4().hex
    # Check if config gives you the keys: 'storage' and 'compute'

    storage_stack = ConfigStorage(config['storage'], algo_ID)
    compute_stack = ConfigCompute(config['compute'], algo_ID)

    template = {
        'Resources': compute_stack
    }
    template['Resources']['FileSystem'] = storage_stack
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
        "SubnetID" : {
            "Description" : "Subnet ID containing resources",
            "Value" : {
                "Ref" : "Subnet"
            }
        },
        "SecurityGroupID" : {
            "Description" : "Security group for custom VPC",
            "Value" : {
                "Ref" : "SecurityGroup"
            }
        },
        "FileSystemName" : {
            "Description" : "S3 Bucket Name",
            "Value" : {
                "Ref" : "FileSystem"
            }
        }
    }


    cf = boto3.client('cloudformation')
    cf.create_stack(
        StackName = f"engine-cfn-{algo_ID}", 
        TemplateBody = json.dumps(template),
        OnFailure = 'DELETE',
        Capabilities = ["CAPABILITY_IAM"]
    )

    return algo_ID



def handler(event, context):

    tbl_name = "UserResourceLog"
    current_datetime = datetime.now().isoformat()

    # Parse JSON
    try:
        request_body = json.loads(event['body'])
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f"Incorrect POST format: got {event}")
        }
        return response

    # Attempt to Provision Resources
    try:
        algo_ID = ProvisionResources(request_body)
        # s3.put_object(Body=request_body['dockerfile'], Bucket=bucket_name, Key=object_key)


    except Exception as e:
        response = {
            'statusCode': 500,
            'body': json.dumps(f'Error provisioning resources: {e}')
        }
        return response

    # Write to table
    try:
        dynamodb = boto3.client('dynamodb')
        item_data = {
            "UserID": {'S': '0'},
            "time": {'S': current_datetime},
            "algo_ID": {'S': algo_ID}
        }
        dynamodb.put_item(TableName=tbl_name, Item=item_data)

        response = {
            'statusCode': 200,
            'body': json.dumps(f'Algo ID {algo_ID}: {request_body}')
        }       
    except Exception as e:
        print(f"Error: {e}")
        response = {
            'statusCode': 500,
            'body': json.dumps(f'Error adding item to DynamoDB table: {e}')
        }
        
    return response



    