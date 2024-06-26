from aws_cdk import (
    Stack,
    aws_cognito as cognito,
)
from constructs import Construct

class UserPool(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = cognito.UserPool.from_user_pool_id(self, "UserPool", "us-east-2_c3KpcMfzh")

        self.api_client = self.user_pool.add_client(
            "APIClient",
            auth_flows = cognito.AuthFlow(user_password = True)
        )
        self.webapp_client = self.user_pool.add_client(
            "WebappClient"
        )


    # Original User Pool
    # self.user_pool = cognito.UserPool(
    #     self, 
    #     "UserPool",
    #     user_pool_name="APIPool",
    #     self_sign_up_enabled=True,
    #     sign_in_aliases={
    #         'email': True,
    #         'username': False
    #     },
    #     standard_attributes={
    #         'email': {
    #             'required': True,
    #             'mutable': True
    #         }
    #     }
    # )