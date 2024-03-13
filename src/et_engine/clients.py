import requests
import boto3


API_ENDPOINT = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/"
COGNITO_CLIENT_ID = "74gp8knmi8qsvl0mn51dnbgqd8"

class Session:

    def __init__(self, credentials):
        
        with open(credentials) as f:
            lines = f.readlines()
            self.user = lines[0].strip()
            self.password = lines[1].strip()

        cognito = boto3.client('cognito-idp')
        auth_response = cognito.initiate_auth(
            ClientId = COGNITO_CLIENT_ID,
            AuthFlow = 'USER_PASSWORD_AUTH',
            AuthParameters = {
                "USERNAME": self.user,
                "PASSWORD": self.password
            }
        )
        # If authentication is successful, extract the tokens
        if auth_response and 'AuthenticationResult' in auth_response:
            self.id_token = auth_response['AuthenticationResult']['IdToken']
            self.access_token = auth_response['AuthenticationResult']['AccessToken']
            self.refresh_token = auth_response['AuthenticationResult'].get('RefreshToken')  # Optional, depends on your Cognito settings
            
        else:
            print("Authentication failed: No authentication result found.")
            return auth_response

class VirtualFileSystemClient(Session):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def connect(self, name):

        # GET enpoint/vfs
        url = API_ENDPOINT + "vfs"
        status = requests.get(url, params={"name": name}, auth=('user', 'pass'))
        return status
        

    def create(self, name):
        url = API_ENDPOINT + "vfs"
        status = requests.post(url, data={"name": name}, auth=(self.user, self.password))
        return status

    def file_exists(self):
        pass


class ToolsClient(Session):
    
    def create(self):
        pass


class Client(Session):

    def __init__(self, credentials):
        super().__init__(credentials)

        self.vfs = VirtualFileSystemClient(credentials)
        self.tools = ToolsClient(credentials)


