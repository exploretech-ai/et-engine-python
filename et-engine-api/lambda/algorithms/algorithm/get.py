import json
import uuid


def handler(event, context):
    '''
    Post request to create new algorithm, store its ID in the database, and return back to the user

    You can pass ?valid=true to return whether or not the ID is valid
    '''


    return {
        'statusCode': 200,
        'body': json.dumps("Lists the info about the algorithm")
    }