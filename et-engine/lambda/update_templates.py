import json
import boto3
import db
import lambda_utils

def update_vfs(cursor):
    sql_query = f"""
        SELECT vfsID FROM VirtualFilesystems
    """
    cursor.execute(sql_query)
    available_vfs = cursor.fetchall()

    
    # Loop through vfs and run boto3 update_stack
    cloudformation = boto3.client('cloudformation')
    for vfs in available_vfs:

        vfs_id = vfs[0]
        vfs_stack_name = "vfs-" + vfs_id

        try:
            parameters = lambda_utils.vfs_template_parameters(vfs_id)
            print("Stack to be updated:", vfs_stack_name)
            print("Parameters:", parameters)

            cloudformation.update_stack(
                StackName=vfs_stack_name, 
                TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/efs-basic.yaml',
                Parameters=parameters,
                Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
            )

        except Exception as e:
            print(f"Error: {e}")


def update_tools(cursor):
    sql_query = f"""
        SELECT toolID FROM Tools
    """
    cursor.execute(sql_query)
    tools = cursor.fetchall()


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
                Parameters=lambda_utils.compute_template_parameters(tool_id),
                Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
            )

        except Exception as e:
            print(f"Error: {e}")


def handler(event, context):
    print('Fetching vfs list')

    # Fetch all vfs from database
    connection = db.connect()
    cursor = connection.cursor()

    try:
        update_vfs(cursor)
        update_tools(cursor)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        cursor.close()
        connection.close()

    

        


