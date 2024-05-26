import json
import boto3
import db
import lambda_utils

def handler(event, context):
    print('Fetching vfs list')

    # Fetch all vfs from database
    connection = db.connect()
    cursor = connection.cursor()
    sql_query = f"""
        SELECT vfsID FROM VirtualFilesystems
    """
    cursor.execute(sql_query)
    available_vfs = cursor.fetchall()

    cursor.close()
    connection.close()

    # Loop through vfs and run boto3 update_stack
    cloudformation = boto3.client('cloudformation')
    for vfs in available_vfs:

        vfs_id = vfs[0]
        vfs_stack_name = "vfs-" + vfs_id

        try:

            print(vfs_stack_name)

            cloudformation.update_stack(
                StackName=vfs_stack_name, 
                TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/efs-basic.yaml',
                Parameters=lambda_utils.vfs_template_parameters(vfs_id),
                Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
            )

        except Exception as e:
            print(f"Error: {e}")


