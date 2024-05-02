import json
import lambda_utils
import boto3

def delete_workflow(tool_id):
    tool_name = "tool-"+tool_id
    
    # Delete S3 Bucket
    lambda_utils.empty_bucket(tool_name)

    # Delete ECR Image
    lambda_utils.delete_repository(tool_name)

    # Delete Stack
    lambda_utils.delete_stack(tool_name)





def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']
        
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
                
                delete_workflow(tool_id)

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
    
