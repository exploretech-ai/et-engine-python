"""
Resources 
https://stackoverflow.com/questions/49082620/how-to-verify-the-signature-of-a-jwt-generated-by-aws-cognito-in-python-3-6
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html
"""

import json
import db
import re
from cryptography.fernet import Fernet
import urllib.request
import jwt
from jwt.algorithms import RSAAlgorithm

region = 'us-east-2'
userpoolId = 'us-east-2_c3KpcMfzh'
appClientId = '7veifuegtpskqerl7b2lakdfdn' 
keysUrl = 'https://cognito-idp.{}.amazonaws.com/{}/.well-known/jwks.json'.format(region, userpoolId)


fernet_key = b'IGE3pGK7ih1vDm4na0EmW-rYCqfnZKMaNR7ea1ose2s='

def handler(event, context):

    # VALIDATE REQUEST
    try:
        token = event['authorizationToken']

        methodArn = event['methodArn'].split(':')
        apiGatewayArnTmp = methodArn[5].split('/')
        awsAccountId = methodArn[4]
        resource = apiGatewayArnTmp[-1]

        print("Resource Requested: " + resource)
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
 
    try:
        connection = db.connect()
        cursor = connection.cursor()
    except Exception as e:
        return {
            'statusCode': 501,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Could not connect to database')
        }
    
    # VALIDATE USER EXISTS
    try:
            
        if "Bearer " in token:
            user = None

            response = urllib.request.urlopen(keysUrl)
            keys = json.loads(response.read())['keys']

            jwtToken = token.split(' ')[-1]
            header = jwt.get_unverified_header(jwtToken)
            kid = header['kid']

            jwkValue = findJwkValue(keys, kid)
            publicKey = RSAAlgorithm.from_jwk(json.dumps(jwkValue))

            decoded = decodeJwtToken(jwtToken, publicKey)
            user_id = decoded['cognito:username']

            source = "web"
            api_key = None

            # >>>>> MORE VALIDATION HERE?
            # <<<<<
  
        else:
            f = Fernet(fernet_key)
            key_id = f.decrypt(token).decode()

            source = "api"
            api_key = token

            cursor.execute(f"""
                SELECT userID FROM APIKeys WHERE keyID = '{key_id}'
            """)

            user_id = cursor.fetchall()[0][0]
            if user_id is None:
                raise NameError(f'no user not associated with key {key_id}')
            
        print("User ID: " + user_id)

    except NameError as e:
        print(e)
        cursor.close()
        connection.close()
        return {
            'statusCode': 401,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Could not authorize userID exists in the database')
        }
    
    except Exception as e:
        print(e)
        cursor.close()
        connection.close()
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

        # >>>>> PREPARE AUTH POLICY (THIS WILL NEED TO CHANGE)
        cursor.execute(f"""
            SELECT allow_tools, allow_vfs FROM Policies WHERE userID = '{user_id}'
        """)

        allow_tools, allow_vfs = cursor.fetchall()[0]
        print(f"allow_tools: {allow_tools}")
        print(f"allow_vfs: {allow_vfs}")

        policy = {
            'keys': {
                'web': True,
                'api': False
            },
            'tools': {
                'web': allow_tools,
                'api': allow_tools
            },
            'vfs': {
                'web': allow_vfs,
                'api': allow_vfs
            }
        }
        
        # >>>>> MODIFY POLICY HERE
        auth_policy.allowAllMethods()
        # <<<<<

        response = auth_policy.build()
        response['context'] = {
            'userID': user_id,
            'source': source
        }
        if api_key is not None:
            response['context']['apiKey'] = api_key
        
        print(response)
        return response


    except Exception as e:
        print(e)
        return {
            'statusCode': 501,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps('Could not build policy')
        }
    
    finally:
        cursor.close()
        connection.close()

                
    


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
        resourcePattern = re.compile(self.pathRegex)
        if not resourcePattern.match(resource):
            raise NameError('Invalid resource path: ' + resource + '. Path should match ' + self.pathRegex)

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
    
        
            