"""
Resources 
https://stackoverflow.com/questions/49082620/how-to-verify-the-signature-of-a-jwt-generated-by-aws-cognito-in-python-3-6
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
"""

import json
import re
import urllib.request
import traceback
import sys
import uuid

region = 'us-east-2'
userpoolId = 'us-east-2_c3KpcMfzh'
appClientId = '7veifuegtpskqerl7b2lakdfdn' 
keysUrl = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, userpoolId)
fernet_key = b'IGE3pGK7ih1vDm4na0EmW-rYCqfnZKMaNR7ea1ose2s='

  
try:
    # These are wrapped in try/catch for unit testing purposes
    from cryptography.fernet import Fernet 
    import jwt
    from jwt.algorithms import RSAAlgorithm
except:
    print('WARNING: could not import cryptography packages')

 
try:
    # These are wrapped in try/catch for unit testing purposes
    import db
    from psycopg2 import sql
    connection = db.connect()
    cursor = connection.cursor()
except Exception as e:
    print('WARNING: Could not connect to database', e)
    cursor = None



def handler(event, context, cursor=cursor, plan='FULL'):

    # VALIDATE REQUEST
    try:
        token = event['authorizationToken']

        methodArn = event['methodArn'].split(':')
        apiGatewayArnTmp = methodArn[5].split('/')
        awsAccountId = methodArn[4]
        resource = '/'.join(apiGatewayArnTmp[3:])
        verb = apiGatewayArnTmp[2]
        print('Event:', event)

        print(f"Request: {verb}/{resource}")
        print(f"Method ARN: {event['methodArn']}")

    except Exception as e:
        print(e)
        return {
            'statusCode': 501,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Could not validate request')
        }

    
    # VALIDATE USER EXISTS
    try:
            
        if "Bearer " in token:
            print('** Bearer Token Found **')

            print('Fetching keys...')
            response = urllib.request.urlopen(keysUrl)
            keys = json.loads(response.read())['keys']

            print('Parsing token...')
            print(token)
            jwtToken = token.split(' ')[-1]
            header = jwt.get_unverified_header(jwtToken)
            kid = header['kid']

            print('Decoding token...')
            jwkValue = findJwkValue(keys, kid)
            publicKey = RSAAlgorithm.from_jwk(json.dumps(jwkValue))

            decoded = decodeJwtToken(jwtToken, publicKey)
            user_id = decoded['cognito:username']
            print('User ID found: ', user_id)

            source = "web"
            api_key = None
  
        else:
            print("** API Key Assumed **")
            user_id = decode_key(cursor, token)
            source = "api"
            api_key = token
            

    except NameError as e:
        print('NAME ERROR:', e)
        return {
            'statusCode': 401,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Could not authorize userID exists in the database')
        }
    
    except Exception as e:
        print('Error: ', e)
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Error validating userID')
        }


    # VALIDATE WHETHER USER HAS ACCESS TO REQUESTED RESOURCE (e.g. build policy)
    try:
        auth_policy = AuthPolicy(user_id, awsAccountId)
        auth_policy.restApiId = apiGatewayArnTmp[0]
        auth_policy.region = methodArn[3]
        auth_policy.stage = apiGatewayArnTmp[1]


        # >>>>> MODIFY POLICY HERE
        allow = True

        # Check if requested method is in plan
        if plan == 'RESULTS':
            if 'vfs' not in resource or verb != 'GET':
                allow = False
        elif plan == 'TOOL_USE':
            if 'tools' in resource and (verb == 'DELETE' or verb == 'PUT'):
                allow = False
            elif verb == 'POST' and resource == 'tools':
                allow = False

        # Check if "{vfsID}" or "{toolID}" or "{taskID}" are requested
        is_engine_resource = "/" in resource
        if allow and is_engine_resource:
            allow = check_engine_resource_access(resource, user_id)
            

        if allow:
            auth_policy.allowMethod(verb, resource)
            print('REQUEST ALLOWED')
        else:
            auth_policy.denyMethod(verb, resource)
            print('REQUEST DENIED')
        
        # <<<<<

        response = auth_policy.build()
        response['context'] = {
            'userID': user_id,
            'source': source
        }
        if api_key is not None:
            response['context']['apiKey'] = api_key
        
        print('Auth Policy: ', response)
        return response


    except Exception as e:
        print('ERROR BUILDING POLICY:', e)
        return {
            'statusCode': 501,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Could not build policy')
        }   


def check_engine_resource_access(resource, user_id):
    print(f'Checking whether user {user_id} has access to resource {resource}')
    resource_type = get_resource_type(resource)
    resource_id = resource.split("/")[1]

    table_map = {
        'vfs': 'VirtualFileSystems',
        'tools': 'Tools',
        'tasks': 'Tasks'
    }
    column_map = {
        'vfs': 'vfsID',
        'tools': 'toolID',
        'tasks': 'taskID'
    }
    table_name = table_map[resource_type]
    column_name = column_map[resource_type]

    sql_query = sql.SQL(
        "SELECT * FROM {table_name} WHERE userID = %s AND {column_name} = %s"
    ).format(
        table_name=sql.SQL(table_name), 
        column_name=sql.SQL(column_name)
    )
    cursor.execute(sql_query, (user_id, resource_id,))
    owned_rows = cursor.fetchall()
    print(f"Found {len(owned_rows)} owned resources of type '{resource_type}' in table {table_name} with resource ID {resource_id}")
    
    
    sql_query = "SELECT * FROM Sharing WHERE granteeID = %s AND resource_type = %s AND resourceID = %s"
    cursor.execute(sql_query, (user_id, resource_type, resource_id,))
    shared_rows = cursor.fetchall()
    print(f"Found {len(shared_rows)} resources of type '{resource_type}' with resource ID {resource_id} granted to user {user_id}")

    if len(owned_rows) == 0 and len(shared_rows) == 0:
        return False
    else:
        return True

def get_resource_type(resource):
    if "/" not in resource:
        return resource
    else:
        return resource.split('/')[0]
    

def decode_key(cursor, token):
    """
    Helper function to decode the API key. This is wrapped into a separate function to facilitate unit test mocking.
    For this reason, note that this function is not covered by unit tests.
    To implement unit tests, the try/catch statements above need to work on a local machine, which requires a big overhaul of the environment setup.
    This is caused by the fact that psycopg2, cryptography, and jwt require binaries to be installed, which vary from machine to machine.
    """

    print("Decrypting key...")
    f = Fernet(fernet_key)
    key_id = f.decrypt(token).decode()

    api_key = token

    print('Fetching userID associated with key ', api_key)

    cursor.execute("SELECT userID FROM APIKeys WHERE keyID = %s", (key_id,))
    if cursor.rowcount == 0:
        raise NameError(f'no user not associated with key {key_id}')      
    else:
        user_id = cursor.fetchall()[0][0]   
        print('User ID found: ', user_id) 

    return user_id


# def get_policy_from_user(cursor, user_id):
#     """
#     Helper function to decode the API key. This is wrapped into a separate function to facilitate unit test mocking.
#     For this reason, note that this function is not covered by unit tests.
#     To implement unit tests, the try/catch statements above need to work on a local machine, which requires a big overhaul of the environment setup.
#     This is caused by the fact that psycopg2, cryptography, and jwt require binaries to be installed, which vary from machine to machine.
#     """
#     cursor.execute("SELECT allow_tools, allow_vfs FROM Policies WHERE userID = %s", (user_id,))
#     return cursor.fetchall()[0]


def findJwkValue(keys, kid):
    for key in keys:
        if key['kid'] == kid:
            return key


def decodeJwtToken(token, publicKey):
    try:
        decoded=jwt.decode(token, publicKey, algorithms=['RS256'], audience=appClientId)
        return decoded
    except Exception as e:
        print(e)
        raise



class HttpVerb:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'
    ALL = '*'
    list = [GET, POST, PUT, PATCH, HEAD, DELETE, OPTIONS]


class AuthPolicy(object):
    # The AWS account id the policy will be generated for. This is used to create the method ARNs.
    awsAccountId = ''
    # The principal used for the policy, this should be a unique identifier for the end user.
    principalId = ''
    # The policy version used for the evaluation. This should always be '2012-10-17'
    version = '2012-10-17'
    # The regular expression used to validate resource paths for the policy
    pathRegex = '^[/.a-zA-Z0-9-\*]+$'

    '''Internal lists of allowed and denied methods.

    These are lists of objects and each object has 2 properties: A resource
    ARN and a nullable conditions statement. The build method processes these
    lists and generates the approriate statements for the final policy.
    '''
    allowMethods = []
    denyMethods = []

    # The API Gateway API id. By default this is set to '*'
    restApiId = 't2pfsy11r1'
    # The region where the API is deployed. By default this is set to '*'
    region = 'us-east-2'
    # The name of the stage used in the policy. By default this is set to '*'
    stage = 'prod'

    def __init__(self, principal, awsAccountId):
        self.awsAccountId = awsAccountId
        self.principalId = principal
        self.allowMethods = []
        self.denyMethods = []

    def _addMethod(self, effect, verb, resource, conditions):
        '''Adds a method to the internal lists of allowed or denied methods. Each object in
        the internal list contains a resource ARN and a condition statement. The condition
        statement can be null.'''
        if verb != '*' and not hasattr(HttpVerb, verb):
            raise NameError('Invalid HTTP verb ' + verb + '. Allowed verbs in HttpVerb class')
        # resourcePattern = re.compile(self.pathRegex)
        # if not resourcePattern.match(resource):
        #     raise NameError('Invalid resource path: ' + resource + '. Path should match ' + self.pathRegex)

        if resource[:1] == '/':
            resource = resource[1:]

        resourceArn = 'arn:aws:execute-api:{}:{}:{}/{}/{}/{}'.format(self.region, self.awsAccountId, self.restApiId, self.stage, verb, resource)

        if effect.lower() == 'allow':
            self.allowMethods.append({
                'resourceArn': resourceArn,
                'conditions': conditions
            })
        elif effect.lower() == 'deny':
            self.denyMethods.append({
                'resourceArn': resourceArn,
                'conditions': conditions
            })

    def _getEmptyStatement(self, effect):
        '''Returns an empty statement object prepopulated with the correct action and the
        desired effect.'''
        statement = {
            'Action': 'execute-api:Invoke',
            'Effect': effect[:1].upper() + effect[1:].lower(),
            'Resource': []
        }

        return statement

    def _getStatementForEffect(self, effect, methods):
        '''This function loops over an array of objects containing a resourceArn and
        conditions statement and generates the array of statements for the policy.'''
        statements = []

        if len(methods) > 0:
            statement = self._getEmptyStatement(effect)

            for curMethod in methods:
                if curMethod['conditions'] is None or len(curMethod['conditions']) == 0:
                    statement['Resource'].append(curMethod['resourceArn'])
                else:
                    conditionalStatement = self._getEmptyStatement(effect)
                    conditionalStatement['Resource'].append(curMethod['resourceArn'])
                    conditionalStatement['Condition'] = curMethod['conditions']
                    statements.append(conditionalStatement)

            if statement['Resource']:
                statements.append(statement)

        return statements

    def allowAllMethods(self):
        '''Adds a '*' allow to the policy to authorize access to all methods of an API'''
        self._addMethod('Allow', HttpVerb.ALL, '*', [])

    def denyAllMethods(self):
        '''Adds a '*' allow to the policy to deny access to all methods of an API'''
        self._addMethod('Deny', HttpVerb.ALL, '*', [])

    def allowMethod(self, verb, resource):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods for the policy'''
        self._addMethod('Allow', verb, resource, [])

    def denyMethod(self, verb, resource):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods for the policy'''
        self._addMethod('Deny', verb, resource, [])

    def allowMethodWithConditions(self, verb, resource, conditions):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of allowed
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition'''
        self._addMethod('Allow', verb, resource, conditions)

    def denyMethodWithConditions(self, verb, resource, conditions):
        '''Adds an API Gateway method (Http verb + Resource path) to the list of denied
        methods and includes a condition for the policy statement. More on AWS policy
        conditions here: http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements.html#Condition'''
        self._addMethod('Deny', verb, resource, conditions)

    def build(self):
        '''Generates the policy document based on the internal lists of allowed and denied
        conditions. This will generate a policy with two main statements for the effect:
        one statement for Allow and one statement for Deny.
        Methods that includes conditions will have their own statement in the policy.'''
        if ((self.allowMethods is None or len(self.allowMethods) == 0) and
                (self.denyMethods is None or len(self.denyMethods) == 0)):
            raise NameError('No statements defined for the policy')

        policy = {
            'principalId': self.principalId,
            'policyDocument': {
                'Version': self.version,
                'Statement': []
            }
        }

        policy['policyDocument']['Statement'].extend(self._getStatementForEffect('Allow', self.allowMethods))
        policy['policyDocument']['Statement'].extend(self._getStatementForEffect('Deny', self.denyMethods))

        return policy
    
        
            