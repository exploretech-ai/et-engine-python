import lambda_utils
import json
import os
import boto3


def to_hierarchy(directory_contents):
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


def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        vfs_id = event['pathParameters']['vfsID']

        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:

            if 'name' in event['queryStringParameters']:
                vfs_name = event['queryStringParameters']['name']
                vfs_id = lambda_utils.get_vfs_id(user, vfs_name)
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(vfs_id)
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps("Error: Invalid query string")
                }
        else:
            available_vfs = lambda_utils.list_vfs(user)
            vfs_name = lambda_utils.get_vfs_name(user, vfs_id)
            if vfs_name not in available_vfs:
                return {
                    'statusCode': 403,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps('VFS unavailable')
                }

            s3 = boto3.client('s3')
            bucket_name = "vfs-" + vfs_id
            directory_contents = s3.list_objects_v2(
                Bucket=bucket_name
            )
            hierarchy = to_hierarchy(directory_contents)

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(hierarchy)
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Error: {e}')
        }
    
if __name__ == "__main__":
    files = [
    ]

    directory = []
    for file in files:
        directory.append(file.split('/'))


    hierarchy = {}
    for file in directory:
        current_branch = hierarchy
        for component in file[:-1]:
            if component in current_branch:
                current_branch = current_branch[component]
            else:
                current_branch[component] = {}
                current_branch = current_branch[component]
        current_branch[file[-1]] = None

    print(hierarchy)

        