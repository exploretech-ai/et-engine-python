import json
import boto3


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



def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']
        tool_id = event['pathParameters']['toolID']

        print('Checking ECR to see if the tool image is ready...')
        tool_is_ready = check_ecr(tool_id)
        print('result:', tool_is_ready)

        print('Checking the most recent Codebuild build status...')
        build_status = check_codebuild(tool_id)
        print('result:', build_status)

        tool_parameters = {
            'ready': tool_is_ready,
            'buildStatus': build_status
        }
        print('Returning the following JSON:', tool_parameters)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(tool_parameters)
        }
        
    except Exception as e:
        print('Error describing tool:', e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Error describing tool')
        }
    