import json
import db

def handler(event, context):

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*'
        },
        'body' : json.dumps("hello, world")
    }