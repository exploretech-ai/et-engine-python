import requests
import boto3
import json

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
            
        else:
            print(f"Authentication failed: {auth_response}")

class VirtualFileSystemClient:

    def __init__(self, session):
        self.session = session

    def connect(self, name):

        # GET enpoint/vfs
        url = API_ENDPOINT + "vfs"
        status = requests.get(url, params={"name": name}, auth=('user', 'pass'))
        return status
        

    def create(self, name):
        url = API_ENDPOINT + "vfs"
        status = requests.post(
            url, 
            data=json.dumps({"name": name}), 
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        return status

    def file_exists(self):
        pass


class ToolsClient:

    def __init__(self, session):
        self.session = session
    
    def create(self):
        pass


class Client(Session):

    def __init__(self, credentials):
        super().__init__(credentials)

        self.vfs = VirtualFileSystemClient(self)
        self.tools = ToolsClient(self)


