import json
import lambda_utils
import db


def delete_tool(tool_id):
    tool_name = "tool-"+tool_id
    print(f'Tool Name: {tool_name}')
    
    # Delete S3 Bucket
    print(f'Deleting S3 Bucket')
    lambda_utils.empty_bucket(tool_name)

    # Delete ECR Image
    print('Deleting ECR Image')
    lambda_utils.delete_repository(tool_name)

    # Delete Stack
    print('Deleting Stack')
    lambda_utils.delete_stack(tool_name)


def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:
        user = event['requestContext']['authorizer']['userID']
        print(f'User ID: {user}')
        
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:
            
            if 'name' in event['queryStringParameters']:
                tool_name = event['queryStringParameters']['name']

                sql_query = f"""
                    SELECT toolID FROM Tools WHERE userID = '{user}' AND name = '{tool_name}'
                """
                cursor.execute(sql_query)
                tool_id = cursor.fetchall()
                
                if len(tool_id) == 0:
                    raise NameError('no tool id found')
                else:
                    tool_id = tool_id[0][0]
                    print(f"Delete Requested for Tool ID: {tool_id}")
                
                

                sql_query = f"""
                    DELETE FROM Tools WHERE userID = '{user}' AND name = '{tool_name}'
                """
                cursor.execute(sql_query)
                connection.commit()
                print("Tool deleted from database")

                delete_tool(tool_id)
                print("Tool successfully deleted")

                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(f"'{tool_name}' deleted")
                }
            else:
                return {
                    'statusCode': 501,
                    'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps("Error: Invalid query string")
                }
        else:
            return {
                'statusCode': 502,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps("Error: must include query string")
            }
        
    except NameError as e:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Tool not found')
        }
    except Exception as e:
        print('ERROR:', e)
        return {
            'statusCode': 503,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'An unknown error occurred while deleting the tool')
        }
    finally:
        cursor.close()
        connection.close()
    
