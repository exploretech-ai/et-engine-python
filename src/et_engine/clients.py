import requests
import boto3
import json


from .vfs import VirtualFileSystem
from .tools import Tool

class VirtualFileSystemClient:

    def __init__(self, session):
        self.session = session
        self.url = session.API_ENDPOINT + "vfs"

    def connect(self, name):

        # query 'name' and return the vfsID, wrap it into a VirtualFileSystem object and return to user
        status = requests.get(
            self.url, 
            params={'name':name},
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )

        return VirtualFileSystem(status.json(), self.session)
        

    def create(self, name):
        
        status = requests.post(
            self.url, 
            data=json.dumps({"name": name}), 
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        return status
    
    def list(self):
        status = requests.get(
            self.url,
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        return status
    
    def delete(self, name):
        status = requests.delete(
            self.url,
            params={'name':name},
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )
        return status

    


class ToolsClient:

    def __init__(self, session):
        self.session = session
        self.url = session.API_ENDPOINT + "tools"
    
    def create(self, name, description):

       
        # API Request
        response = requests.post(
            self.url, 
            data=json.dumps({
                "name": name,
                "description": description
            }), 
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )

        return response
        

    def connect(self, name):
        status = requests.get(
            self.url, 
            params={'name':name},
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )

        return Tool(status.json(), self.session)

    def list(self):
        pass

    def delete(self):
        pass


class Client:

    API_ENDPOINT = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/"
    COGNITO_CLIENT_ID = "74gp8knmi8qsvl0mn51dnbgqd8"


    def __init__(self, credentials):
        
        with open(credentials) as f:
            lines = f.readlines()
            self.user = lines[0].strip()
            self.password = lines[1].strip()

        cognito = boto3.client('cognito-idp')
        auth_response = cognito.initiate_auth(
            ClientId = self.COGNITO_CLIENT_ID,
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
            self.vfs = VirtualFileSystemClient(self)
            self.tools = ToolsClient(self)
            
        else:
            print(f"Authentication failed: {auth_response}")

        


