import json

def handler(event, context):
    """
    You can pass ?valid=true to return whether or not the ID is valid
    """

    try:
            
        # test_validity = event['queryStringParameters']['valid'] if 'valid' in event['queryStringParameters'] else None

        return {
                'statusCode': 200,
                'body': json.dumps(event['body'])
            }
    except Exception as e:
        return {
                'statusCode': 500,
                'body': json.dumps(f"Error: {e}")
            }


# import json

# def handler(event, context):
#     return {
#         'statusCode': 200,
#         'body': json.dumps("hello, world")
#     }