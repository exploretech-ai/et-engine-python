import json
import db
import uuid
import datetime

class SelfShareError(Exception):
    pass
class AlreadyExistsError(Exception):
    pass

def handler(event, context):

    try:
        connection = db.connect()
        cursor = connection.cursor()

        if 'body' in event:
            body = json.loads(event['body'])
        else:
            raise Exception('request body empty')
        
        if 'grantee' in body:
            grantee = body['grantee']
        else:
            raise Exception('request body does not contain key "grantee"')
        
        # throws an error if poorly-formed UUID
        uuid.UUID(grantee, version=4)
        

        accessID = str(uuid.uuid4())
        ownerID = event['requestContext']['authorizer']['userID']
        granteeID = grantee
        resource_type = "tools"
        resourceID = event['pathParameters']['toolID']
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

    