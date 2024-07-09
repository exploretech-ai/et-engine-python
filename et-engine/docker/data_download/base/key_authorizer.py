"""
Resources 
https://stackoverflow.com/questions/49082620/how-to-verify-the-signature-of-a-jwt-generated-by-aws-cognito-in-python-3-6
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
"""
from werkzeug.wrappers import Request, Response

import json
import urllib.request
import logging

from psycopg2 import sql
from cryptography.fernet import Fernet 
import jwt
from jwt.algorithms import RSAAlgorithm

from . import FERNET_KEY, CONNECTION_POOL

logger = logging.getLogger()
logger.setLevel(logging.INFO)


RESOURCE_TO_TABLE_NAME = {
    'vfs': 'VirtualFileSystems',
    'tools': 'Tools',
    'tasks': 'Tasks',
    'keys': "APIKeys" # ?????
}
RESOURCE_TO_TABLE_COLUMN = {
    'vfs': 'vfsID',
    'tools': 'toolID',
    'tasks': 'taskID',
    'keys': 'keyID' # ?????
}


class AuthMiddleware:


    region = 'us-east-2'
    user_pool_id = 'us-east-2_c3KpcMfzh'
    app_client_id = '2ttoam3d4k75fcf2106nmpned' 
    keys_url = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, user_pool_id)
    fernet_key = FERNET_KEY


    def __init__(self, app):

        self.app = app


    def __call__(self, environ, start_response):

        request = Request(environ)
        resource = request.path
        verb = request.method

        # Request can use either Bearer token (OAuth2) or Authorization token (API Key)
        auth_header = request.headers.get('Authorization')
        bearer_header = request.headers.get('Bearer')
       
        # Check headers
        valid_headers, invalid_header_response = self.validate_headers(auth_header, bearer_header)
        if not valid_headers:
            return invalid_header_response(environ, start_response)
        
        # Authenticate user
        authenticated, authentication_error_response, user_id = self.authenticate(auth_header, bearer_header)
        if not authenticated:
            return authentication_error_response(environ, start_response)
        
        # Check if user has access to resources
        authorized, unauthorized_response = self.authorize(user_id, resource, verb)
        if authorized:
            return self.app(environ, start_response)
        else:
            return unauthorized_response(environ, start_response)
        
        
    def validate_headers(self, auth_token, bearer_token):
        
        if auth_token is not None and bearer_token is not None:
            return False, Response("Cannot have both Authorization and Bearer tokens", status=401)
        
        if auth_token is None and bearer_token is None:
            return False, Response("Missing authorization token", status=401)
        
        return True, None
    
    
    def authenticate(self, auth_token, bearer_token):

        if auth_token and bearer_token is None:
            return self.authenticate_api_key(auth_token)
        
        elif bearer_token and auth_token is None:
            return self.authenticate_bearer(bearer_token)
        
        else:
            return False, Response("Unknown authentication error", status=401), None
        
    
    def authenticate_api_key(self, auth_token):

        try:
            user_id = self.decode_api_key(auth_token)

        except NameError as e:
            return False, Response("User not found", status=401)
        
        except Exception as e:
            return False, Response("Unknown authentication error in API key", status=401)
        
        source = "api"
        api_key = auth_token

        return True, None, user_id


    def authenticate_bearer(self, bearer_token):

        try:
            user_id = self.decode_bearer_token(bearer_token)

        except Exception as e:
            return False, Response("Unknown authentication error in Bearer token", status=401)
        
        source = "web"
        api_key = None

        return True, None, user_id
    

    def authorize(self, user_id, resource, verb):

        # Check user's plan against requested method
        plan_allows_access = check_plan_access(user_id, resource, verb)
        if not plan_allows_access:
            return False, Response("Access denied", status=403)

        # Check user's access to a specific resource
        user_can_access_resource, authorization_error_response = check_engine_resource_access(resource, user_id)        
        if user_can_access_resource:
            return True, None
        else:
            return False, authorization_error_response
        
    
    def decode_api_key(self, token):
        """
        Helper function to decode the API key. This is wrapped into a separate function to facilitate unit test mocking.
        For this reason, note that this function is not covered by unit tests.
        To implement unit tests, the try/catch statements above need to work on a local machine, which requires a big overhaul of the environment setup.
        This is caused by the fact that psycopg2, cryptography, and jwt require binaries to be installed, which vary from machine to machine.
        """

        f = Fernet(self.fernet_key)
        key_id = f.decrypt(token).decode()

        connection = CONNECTION_POOL.getconn()
        cursor = connection.cursor()

        try:
            
            cursor.execute("SELECT userID FROM APIKeys WHERE keyID = %s", (key_id,))
            
            if cursor.rowcount == 0:
                raise NameError(f'no user not associated with key {key_id}')      
            
            else:
                user_id = cursor.fetchall()[0][0]   

            return user_id
        
        except Exception as e:
            raise e
        
        finally:
            cursor.close()
            CONNECTION_POOL.putconn(connection)
             

    def decode_bearer_token(self, bearer_token):

        # Load JSON keys
        response = urllib.request.urlopen(self.keys_url)
        keys = json.loads(response.read())['keys']

        # Extract header
        jwt_token = bearer_token.split(' ')[-1]
        header = jwt.get_unverified_header(jwt_token)
        kid = header['kid']

        # Decode remainder of token
        jwk_value = self.find_jwk_value(keys, kid)
        public_key = RSAAlgorithm.from_jwk(json.dumps(jwk_value))
        decoded = self.decode_jwt_token(jwt_token, public_key)

        user_id = decoded['cognito:username']
        return user_id
    

    def find_jwk_value(self, keys, kid):
        for key in keys:
            if key['kid'] == kid:
                return key


    def decode_jwt_token(self, token, public_key):
        
        try:
            decoded=jwt.decode(token, public_key, algorithms=['RS256'], audience=self.app_client_id)
            return decoded
        
        except Exception as e:
            raise


def get_user_plan(user_id):
    return 'FULL'


def check_plan_access(user_id, resource, verb):
    """
    Plans are 'FULL', 'RESULTS', and 'TOOL_USE'
    * NOTE: only FULL is implemented, but this method could be configured for different plans
    """

    user_plan = get_user_plan(user_id)

    allow = True

    if user_plan == 'RESULTS':
        if 'vfs' not in resource or verb != 'GET' or '/share' in resource:
            allow = False

    elif user_plan == 'TOOL_USE':
        if 'tools' in resource and (verb == 'DELETE' or verb == 'PUT'):
            allow = False
        elif verb == 'POST' and resource == 'tools':
            allow = False
        if '/share' in resource:
            allow = False

    return allow
 

def check_engine_resource_access(resource, user_id):

    # Split path up by slashes
    resource_path = resource.strip("/").split("/")

    # Allows any user that's made it this far access to access base methods
    if not resource_path[0] or len(resource_path) == 1:
        return True, None

    # Extract useful parameters from path
    resource_type = resource_path[0]
    resource_id = resource_path[1]

    table_name = RESOURCE_TO_TABLE_NAME[resource_type]
    column_name = RESOURCE_TO_TABLE_COLUMN[resource_type]

    # Query the databse to authorize
    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:

        # Check if the user owns this resource
        cursor.execute(
            sql.SQL(
                "SELECT * FROM {table_name} WHERE userID = %s AND {column_name} = %s"
            ).format(
                table_name=sql.SQL(table_name), 
                column_name=sql.SQL(column_name)
            ), 
            (user_id, resource_id,)
        )

        if cursor.rowcount > 1:
            return False, Response("Unknown authentication error", status=401)
        
        elif cursor.rowcount == 1:
            return True, None    

        # Check if the requested resource was shared with this user
        cursor.execute(
            "SELECT * FROM Sharing WHERE granteeID = %s AND resource_type = %s AND resourceID = %s",
            (user_id, resource_type, resource_id,)
        )
        if cursor.rowcount > 1:
            return False, Response("Unknown authentication error", status=401)
        
        elif cursor.rowcount == 1:
            return True, None
        
        else:
            return False, Response("Access denied", status=403)
        
    except Exception as e:
        raise e
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)
    