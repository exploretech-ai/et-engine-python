import requests
import boto3
import json
import os

from .vfs import VirtualFileSystem
from .tools import Tool

class VirtualFileSystemClient:

    def __init__(self, client):
        self.session = client.session
        self.url = client.API_ENDPOINT + "vfs"
        self.client = client

    def connect(self, name):

        # query 'name' and return the vfsID, wrap it into a VirtualFileSystem object and return to user
        status = requests.get(
            self.url, 
            params={'name':name},
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )

        return VirtualFileSystem(status.json(), self.client)
        

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
    """Client to the ET Tools API

    Attributes
    ----------
    session : Session
        Authenticated session for the client
    url : string
        URL to the ET Tools API
    
    """

    def __init__(self, client):
        """Tools client constructor
        
        Parameters 
        ----------
        session : client
            Authenticated base client
        

        """
        self.client = client
        self.session = client.session
        self.url = client.API_ENDPOINT + "tools"
    
    def create(self, name, description):
        """Creates a new Tool
        
        Parameters
        ----------
        name : string
            Name of the tool
        description : string
            Plain text description of the tool

        Returns
        -------
        Tool
            A Tool object connected to the newly-created tool

        Raises
        ------

        Warnings
        --------
        The API works, but the method does not yet return a connected "Tool" object
        """
       
        # API Request
        response = requests.post(
            self.url, 
            data=json.dumps({
                "name": name,
                "description": description
            }), 
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )

        # >>>>>
        # HERE I NEED TO POST-PROCESS THE RESPONSE AND TURN IT INTO A TOOL
        # MAKE SURE TO HANDLE EXCEPTIONS
        # <<<<<

        return response
        

    def connect(self, name):
        status = requests.get(
            self.url, 
            params={'name':name},
            headers={"Authorization": f"Bearer {self.session.id_token}"}
        )

        return Tool(status.json(), self.client)

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


class Session:
    """Holds session credentials for the ET Engine Client

    Attributes
    ----------
    user : string
        The username associated with the session
    password : string
        The password associated with the user
    id_token : string
        The authenticated ID token for the session
    access_token : string
        The authenticated access token for the session
    """
    COGNITO_CLIENT_ID = "74gp8knmi8qsvl0mn51dnbgqd8"

    def __init__(self, credentials = None):
        """Authenticates and starts a session
        
        Parameters
        ----------
        credentials : string
            Path to a file containing the credentials (username in line 1, password in line 2)

        Raises
        ----------
        Exception
            Authentication error
        """
        
        if credentials is None:
            try:
                self.id_token = os.environ['ET_ENGINE_TOKEN']
            except KeyError as e:
                raise Exception('ET_ENGINE_TOKEN must be set if no credentials file is provided')
            return 

        with open(credentials) as f:
            lines = f.readlines()
            user = lines[0].strip()
            password = lines[1].strip()
        
        cognito = boto3.client(
            'cognito-idp',
            region_name='us-east-2'
        )
        auth_response = cognito.initiate_auth(
            ClientId = self.COGNITO_CLIENT_ID,
            AuthFlow = 'USER_PASSWORD_AUTH',
            AuthParameters = {
                "USERNAME": user,
                "PASSWORD": password
            }
        )
        

        # If authentication is successful, extract the tokens
        if auth_response and 'AuthenticationResult' in auth_response:
            self.id_token = auth_response['AuthenticationResult']['IdToken']
            self.access_token = auth_response['AuthenticationResult']['AccessToken']
        else:
            raise Exception(f"Authentication failed: {auth_response}")

class Client:
    """Base Client for accessing all the ET Engine features
    
    Attributes
    ----------
    API_ENDPOINT : string
        URL to the API base
    COGNITO_CLIENT_ID : string
        Client ID associated with the cognito user pool that controls API access
    session : Session
        Authenticated session, including tokens
    vfs : VirtualFileSystemClient
        The ET Virtual File Systems client
    tools : ToolsClient
        The ET Tools client

    
    """

    API_ENDPOINT = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/"
    


    def __init__(self, credentials = None):
        """Initializes the ET Engine API Client by authenticating the user and starting a session
        
        Parameters
        ----------
        credentials : string
            Path to a file containing the credentials (username in line 1, password in line 2)

        Returns
        ----------
        Client
            An authenticated client for interacting with the ET Engine API

        Raises
        ----------
        Exception
            Authentication error
            
        """

        self.session = Session(credentials)
        
        self.vfs = VirtualFileSystemClient(self)
        self.tools = ToolsClient(self)
            
        

        


