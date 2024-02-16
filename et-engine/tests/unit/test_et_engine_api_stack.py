import aws_cdk as core
import aws_cdk.assertions as assertions

from et_engine_api.et_engine_api_stack import EtEngineApiStack

# example tests. To run these tests, uncomment this file along with the example
# resource in et_engine_api/et_engine_api_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EtEngineApiStack(app, "et-engine-api")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
