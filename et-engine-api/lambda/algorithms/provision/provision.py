import json

def handler(event, context):

    

    return {
        'statusCode': 200,
        'body': json.dumps("This request will provision the provided algoID")
    }

