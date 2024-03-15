import json
import lambda_utils

def empty_bucket(vfs_id):
    bucket_name = "vfs-" + vfs_id

def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:

            # if 'id' in event['queryStringParameters']:
            #     vfs_id = event['queryStringParameters']['id']
            #     lambda_utils.delete_by_id(user, vfs_id)
            #     return {
            #         'statusCode': 200,
            #         'body': json.dumps(f"'{vfs_id}' deleted")
            #     }
            
            if 'name' in event['queryStringParameters']:
                tool_name = event['queryStringParameters']['name']
                tool_id = lambda_utils.get_tool_id(user, tool_name)
                
                empty_bucket(tool_id)
                lambda_utils.delete_tool_by_id(user, tool_id)

                return {
                    'statusCode': 200,
                    'body': json.dumps(f"'{tool_name}' deleted")
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps("Error: Invalid query string")
                }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps("Error: must include query string")
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {e}')
        }
    
