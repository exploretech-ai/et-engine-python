
import json
import boto3
import db
import lambda_utils
import uuid

# def get_user(event):
#     cognito = boto3.client('cognito-idp')
#     response = cognito.get_user(
#         AccessToken=event['authorizationToken']
#     )

def handler(event, context):
    """
    creates a new filesystem under the specified user
    """

    # Get user
    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        body = json.loads(event['body'])
        tool_name = body['name']
        tool_description = body['description']
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Parse Error: {e}')
        }


    # List all available vfs
    try:
        # available_tools = lambda_utils.list_tools(user)

        # check if name is in available_vfs
        # if tool_name in available_tools:
        if False:
            return {
                'statusCode': 500,
                'body': json.dumps(f"Failed: '{tool_name}' already exists")
            }
        
        else:

            tool_id = str(uuid.uuid4())

            # connection = db.connect()
            # cursor = connection.cursor()
            # sql_query = f"""
            #     INSERT INTO VirtualFileSystems (toolID, userID, name, description)
            #     VALUES ('{tool_id}', '{user}', '{tool_name}', '{tool_description})
            # """
            # cursor.execute(sql_query)
            # connection.commit()
            # cursor.close()
            # connection.close()

            # >>>>> s3 bucket added to cfn stack
            # Use create_stack to create the codebuild workflow here
            cfn = boto3.client('cloudformation')
            
            cfn.create_stack(
                StackName='tool-' + tool_id,
                TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/compute-basic.yaml',
                Parameters=[
                    {
                        'ParameterKey': 'toolID',
                        'ParameterValue': tool_id
                    },
                ],
                Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
            )

            return {
                'statusCode': 200,
                'body': json.dumps(tool_id)
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Creation Error: {e}')
        }



    # Check if "name" is in vfs & return error if so

    # If "name" is not in vfs:
    #     1. Generate vfsID
    #     2. Push [vfsID, name, userID] to table
    #     3. Create new s3 bucket
    #     4. Return vfsID

    return {
        'statusCode': 200,
        'body': json.dumps('hello, world')
    }