import json
import lambda_utils
import boto3





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
                vfs_name = event['queryStringParameters']['name']
                vfs_id = lambda_utils.get_vfs_id(user, vfs_name)
                
                lambda_utils.empty_bucket("vfs-"+vfs_id)
                lambda_utils.delete_by_id(user, vfs_id)

                return {
                    'statusCode': 200,
                    'body': json.dumps(f"'{vfs_name}' deleted")
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
    
