import json
import boto3


def get_stack():
    
    s3 = boto3.client('s3')
    return s3.get_object(Bucket="computemodule-codebucketff4c7ad6-kh9e9qicppyn", Key="cfn/Module-Compute.template.json")

def handler(event, context):
    """
    TODO
    This method does the following:
    
    1. reads the algo JSON from the database (algorithms table)
    2. converts the JSON to a cloudformation stack
    3. deploys the cloudformation stack 
    """

    try:
        workflowID = event['pathParameters']['workflowID']

        # TODO
        # read the workflow graph from the DB
        # use nodes to fetch computing templates
        # ----

        # stack = ProvisionResources(algoID)
        stack = get_stack()
        stack = stack['Body'].read().decode('utf-8')


        cf = boto3.client('cloudformation')
        cf.create_stack(
            StackName = f"engine-workflow-{workflowID}", 
            TemplateBody = stack,
            OnFailure = 'DELETE',
            Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
        )

        return {
            'statusCode': 200,
            'body': json.dumps("provision started")
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {e}")
        }


if __name__ == "__main__":

    stack = get_stack()
    stack = stack['Body'].read().decode('utf-8')


    cf = boto3.client('cloudformation')
    cf.create_stack(
        StackName = f"engine-algo-0000", 
        TemplateBody = stack,
        OnFailure = 'DELETE',
        Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
    )
