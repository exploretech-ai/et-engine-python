import json
import boto3
import db

def handler(event, context):
    print('Fetching tool list')

    # Fetch all tools from database
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT toolID FROM Tools
    """
    cursor.execute(sql_query)
    tools = cursor.fetchall()

    cursor.close()
    connection.close()

    # Loop through tools and run boto3 update_stack
    cloudformation = boto3.client('cloudformation')
    for tool in tools:

        tool_id = tool[0]
        tool_stack_name = "tool-" + tool_id

        try:

            print(tool_stack_name)

            cloudformation.update_stack(
                StackName=tool_stack_name, 
                TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/compute-basic.yaml',
                Parameters=[
                    {
                        'ParameterKey': 'toolID',
                        'ParameterValue': tool_id
                    },
                ],
                Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
            )

        except Exception as e:
            print(f"Error: {e}")


