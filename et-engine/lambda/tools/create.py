
import json
import boto3
import db
import uuid


def handler(event, context):
    """
    creates a new filesystem under the specified user
    """
    
    try:
        
        user = event['requestContext']['authorizer']['userID']
        print(f'User ID: {user}')

        body = json.loads(event['body'])
        tool_name = body['name']
        tool_description = body['description']

    except Exception as e:
        print(f'PARSE ERROR: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred while parsing the requested tool creation')
        }


    # List all available vfs
    connection = db.connect()
    cursor = connection.cursor()
    try:

        print('Fetching Available Tools..')

        sql_query = f"""
            SELECT name FROM Tools WHERE userID = '{user}'
        """
        cursor.execute(sql_query)
        available_tools = [row[0] for row in cursor.fetchall()]

        # check if name is in available_vfs
        if tool_name in available_tools:
            return {
                'statusCode': 500,
                'body': json.dumps(f"Failed: '{tool_name}' already exists")
            }
        
        else:

            tool_id = str(uuid.uuid4())
            cfn = boto3.client('cloudformation')

            parameters = [
                {
                    'ParameterKey': 'toolID',
                    'ParameterValue': tool_id
                },
            ]
            
            cfn.create_stack(
                StackName='tool-' + tool_id,
                TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/compute-basic.yaml',
                Parameters=parameters,
                Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
            )
            

            sql_query = f"""
                INSERT INTO Tools (toolID, userID, name, description)
                VALUES ('{tool_id}', '{user}', '{tool_name}', '{tool_description}')
            """
            cursor.execute(sql_query)
            connection.commit()
            
            return {
                'statusCode': 200,
                'body': json.dumps(tool_id)
            }
        
    except Exception as e:
        print(f'ERROR: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error creating Tool')
        }
    
    finally:
        cursor.close()
        connection.close()


