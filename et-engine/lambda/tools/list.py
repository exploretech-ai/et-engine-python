import lambda_utils
import json

def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:

            if 'name' in event['queryStringParameters']:
                tool_name = event['queryStringParameters']['name']
                tool_id = lambda_utils.get_tool_id(user, tool_name)
                return {
                    'statusCode': 200,
                    'body': json.dumps(tool_id)
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps("Error: Invalid query string")
                }
        else:
            available_vfs = lambda_utils.list_tools(user)
            return {
                'statusCode': 200,
                'body': json.dumps(available_vfs)
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {e}')
        }
    
