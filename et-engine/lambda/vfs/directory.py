import lambda_utils
import json
import os
import boto3




def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']
        vfs_id = event['pathParameters']['vfsID']
        # 

        s3 = boto3.client('s3')
        bucket_name = "vfs-" + vfs_id
        directory_contents = s3.list_objects_v2(
            Bucket=bucket_name
        )
        hierarchy = lambda_utils.to_hierarchy(directory_contents)

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

        