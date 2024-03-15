import aws_cdk as core
import aws_cdk.assertions as assertions

from compute_basic.compute_basic_stack import ComputeBasicStack

# example tests. To run these tests, uncomment this file along with the example
# resource in compute_basic/compute_basic_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ComputeBasicStack(app, "compute-basic")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
