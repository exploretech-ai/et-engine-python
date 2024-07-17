import boto3
from botocore.client import ClientError


def get_tool_stack(tool_id):

    cf_client = boto3.client('cloudformation')
    cf_response = cf_client.describe_stacks(StackName=f"tool-{tool_id}")
    cf_outputs = cf_response["Stacks"][0]["Outputs"]
    
    return cf_outputs


def get_stack_outputs(stack_name):

    cf_client = boto3.client('cloudformation')
    cf_response = cf_client.describe_stacks(StackName=stack_name)
    cf_outputs = cf_response["Stacks"][0]["Outputs"]
    
    return cf_outputs


def get_component_from_outputs(outputs, key):
    value = None
    for elem in outputs:
        if elem["OutputKey"] == key:
            value = elem["OutputValue"]

    if value is None:
        raise Exception("Key {key} not found")
    
    return value


def get_tool_components(tool_id, keys):
    outputs = get_tool_stack(tool_id)

    components = {}
    for key in keys:
        components[key] = get_component_from_outputs(outputs, key)
        
    return components
    

def to_hierarchy(directory_contents):
    """Takes an s3-style list of keys and turns it into a hierarchical dict-based directory structure"""
    files = []
    for obj in directory_contents['Contents']:
        files.append(obj['Key'])

    directory = []
    for file in files:
        directory.append(file.split('/'))

    hierarchy = {}
    for file in directory:
        current_branch = hierarchy
        for component in file[:-1]:
            if component not in current_branch:
                current_branch[component] = {}
            current_branch = current_branch[component]
        current_branch[file[-1]] = None

    return hierarchy


def empty_bucket(bucket_name):
    
    try:
        s3 = boto3.resource('s3')

        # Checks if bucket exists, throws a Client Error. If not, runs delete workflow.
        s3.meta.client.head_bucket(Bucket=bucket_name)

        # Actually delete bucket
        bucket = s3.Bucket(bucket_name)
        bucket.objects.all().delete()

    except ClientError:
        print('Bucket already empty')
        

def delete_repository(repo_name):
    """
    Modified from here: https://stackoverflow.com/questions/58843927/boto3-script-to-delete-all-images-which-are-untagged
    """

    ecr = boto3.client('ecr')

    # Checks if bucket exists, throws a Client Error. If not, runs delete workflow.
    repositories = ecr.describe_repositories()

    repository_names = [repo['repositoryName'] for repo in repositories['repositories']]

    if repository_names and repo_name in repository_names:
        images = ecr.list_images(
            repositoryName=repo_name
        )
        if images['imageIds']:
            ecr.batch_delete_image(
                repositoryName=repo_name,
                imageIds=images['imageIds']
            )


def stack_exists(name, required_status = 'CREATE_COMPLETE'):
    cfn = boto3.client('cloudformation')
    try:
        data = cfn.describe_stacks(StackName = name)
    except ClientError:
        return False
    return data['Stacks'][0]['StackStatus'] == required_status


def delete_stack(stack_name):
    
    cfn = boto3.client('cloudformation')

    if stack_exists(stack_name):
        response = cfn.delete_stack(
            StackName=stack_name
        )
        s3 = boto3.client('s3')
        # s3.delete_bucket(Bucket=stack_name)


def compute_template_parameters(tool_id):
    return [
        {
            'ParameterKey': 'toolID',
            'ParameterValue': tool_id
        }
    ]


def vfs_template_parameters(vfs_id):
    engine_stack_outputs = get_stack_outputs("ETEngine")
    vpc_id = get_component_from_outputs(engine_stack_outputs, "ComputeClusterVpcID")
    sg_id = get_component_from_outputs(engine_stack_outputs, "ComputeClusterSgID")
    launch_download_from_s3_to_efs_arn = get_component_from_outputs(engine_stack_outputs, "DownloadS3ToEfsFunctionArn")

    return [
        {
            'ParameterKey': 'vfsID',
            'ParameterValue': vfs_id
        },
        {
            'ParameterKey': 'sgID',
            'ParameterValue': sg_id
        },
        {
            'ParameterKey': 'vpcID',
            'ParameterValue': vpc_id
        },
        {
            'ParameterKey': 'launchDownloadFromS3ToEfsArn',
            'ParameterValue': launch_download_from_s3_to_efs_arn
        },
    ]


def check_ecr(tool_id):
    ecr = boto3.client('ecr')

    ready = False
    image_details = ecr.describe_images(repositoryName="tool-"+tool_id)['imageDetails']
    if image_details:
        ready = True

    return ready


def check_codebuild(tool_id):

    cb = boto3.client('codebuild')
    project_builds = cb.list_builds_for_project(
        projectName="tool-" + tool_id
    )
    project_builds_data = cb.batch_get_builds(
        ids=project_builds['ids']
    )
    build_status = project_builds_data['builds'][0]['buildStatus']

    return build_status


def get_cluster_parameters():
    engine_stack_outputs = get_stack_outputs("ETEngine")

    role_arn = get_component_from_outputs(engine_stack_outputs, "TaskExecutionRoleArn")
    cluster_name = get_component_from_outputs(engine_stack_outputs, "ClusterName")
    capacity_provider_name = get_component_from_outputs(engine_stack_outputs, "CapacityProviderName")

    return {
        'role_arn': role_arn,
        'cluster_name': cluster_name,
        'capacity_provider_name': capacity_provider_name
    }


def get_batch_parameters():
    engine_stack_outputs = get_stack_outputs("ETEngine")

    role_arn = get_component_from_outputs(engine_stack_outputs, "JobRole")

    return {
        'role_arn': role_arn,
    }