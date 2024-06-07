import json
import db
import uuid
import datetime

class SelfShareError(Exception):
    pass
class AlreadyExistsError(Exception):
    pass
class NotOwnerError(Exception):
    pass

def handler(event, context):

    try:
        connection = db.connect()
        cursor = connection.cursor()

        ownerID = event['requestContext']['authorizer']['userID']
        resourceID = event['pathParameters']['toolID']
        resource_type = "tools"
        is_owned = json.loads(event['requestContext']['authorizer']['isOwned'])

        if not is_owned:
            raise NotOwnerError
        print(f'Ownership verified (isOwned = {is_owned})')

        if 'body' in event:
            body = json.loads(event['body'])
        else:
            raise Exception('request body empty')
        
        if 'grantee' in body:
            granteeID = body['grantee']
        else:
            raise Exception('request body does not contain key "grantee"')
                
        # throws an error if poorly-formed UUID
        uuid.UUID(granteeID, version=4)
        print('Grantee ID formatted properly')
        
        accessID = str(uuid.uuid4())
        date_created = datetime.datetime.now()
        date_created = date_created.strftime('%Y-%m-%d %H:%M:%S')

        if ownerID == granteeID:
            raise SelfShareError
        
        query = "SELECT * FROM Sharing WHERE ownerID = %s AND granteeID = %s AND resource_type = %s AND resourceId = %s"
        cursor.execute(query, (ownerID, granteeID, resource_type, resourceID,))
        if cursor.rowcount > 0:
            raise AlreadyExistsError
        

        cursor.execute("""
            INSERT INTO Sharing (accessID, ownerID, granteeID, resource_type, resourceID, date_granted)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            accessID, 
            ownerID, 
            granteeID, 
            resource_type, 
            resourceID, 
            date_created,
        ))
        connection.commit()

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps("success")
        }
    
    except NotOwnerError as e:
        print('ERROR: MUST BE OWNER OF RESOURCE TO SHARE', e)
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps("must be owner to share")
        }

    except SelfShareError as e:
        print('TRIED TO SHARE WITH SELF, ABORTED:', e)
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps("cannot share with self")
        }
    
    except AlreadyExistsError as e:
        print('RESOURCE HAS ALREADY BEEN SHARED:', e)
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps("resource has already been shared")
        }
    
    except ValueError as e:
        print('INVALID GRANTEE ID: must be uuid4', e)
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps("Invalid grantee")
        }
    except Exception as e:
        print('ERROR:', e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps("Internal server error")
        }
    
    finally:
        cursor.close()
        connection.close()

    