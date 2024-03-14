import lambda_utils
import json

def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:

            if 'name' in event['queryStringParameters']:
                vfs_name = event['queryStringParameters']['name']
                vfs_id = lambda_utils.get_vfs_id(user, vfs_name)
                return {
                    'statusCode': 200,
                    'body': json.dumps(vfs_id)
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps("Error: Invalid query string")
                }
        else:
            available_vfs = lambda_utils.list_vfs(user)
            return {
                'statusCode': 200,
                'body': json.dumps(available_vfs)
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {e}')
        }
    
