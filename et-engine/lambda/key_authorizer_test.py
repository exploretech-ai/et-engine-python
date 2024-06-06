import key_authorizer
import os
from unittest.mock import patch
import pytest
import uuid

"""
Plan Access Matrix
------------------
                                    SERVICES        SERVICES            
                                    Results Only    Tool Development    Full Developer Access
DELETE/keys                         -               o                   o
GET/keys                            -               o                   o
POST/keys                           -               o                   o
DELETE/tasks                        -               o                   o
GET/tasks                           -               o                   o
GET/tasks/{taskID}                  -               o                   o
DELETE/tools                        -               -                   o
GET/tools                           -               o                   o
POST/tools                          -               -                   o
GET/tools/{toolID}                  -               o                   o
POST/tools/{toolID}                 -               o                   o
PUT/tools/{toolID}                  -               -                   o
DELETE/vfs                          -               o                   o
GET/vfs                             o               o                   o
POST/vfs                            -               o                   o
GET/vfs/{vfsID}                     o               o                   o
POST/vfs/{vfsID}                    -               o                   o
DELETE/vfs/{vfsID}/{filepath+}      -               o                   o
GET/vfs/{vfsID}/list                o               o                   o
POST/vfs/{vfsID}/mkdir              -               o                   o


Sample policy document:

expected_response = {
    'principalId': user_id,
    'policyDocument': {
        'Version': '2012-10-17', 
        'Statement': [
            {
                'Action': 'execute-api:Invoke', 
                'Effect': 'Allow', 
                'Resource': [
                    'arn:aws:execute-api:us-east-2:734818840861:t2pfsy11r1/prod/*/*'
                ]
            }
        ]
    }, 
    'context': {
        'userID': user_id, 
        'source': 'api', 
        'apiKey': api_key
    }        
}


"""


ARN_BASE = 'arn:aws:execute-api:us-east-2:734818840861:t2pfsy11r1/prod/'
ENDPOINTS = [
    'DELETE/keys',
    'GET/keys',
    'POST/keys',
    'DELETE/tasks',
    'GET/tasks',
    'GET/tasks/' + str(uuid.uuid4()),
    'DELETE/tools',
    'GET/tools',
    'POST/tools',
    'GET/tools/' + str(uuid.uuid4()),
    'POST/tools/' + str(uuid.uuid4()),
    'PUT/tools/' + str(uuid.uuid4()),
    'DELETE/vfs',
    'GET/vfs',
    'POST/vfs',
    'GET/vfs/' + str(uuid.uuid4()),
    'POST/vfs/' + str(uuid.uuid4()),
    f'DELETE/vfs/{str(uuid.uuid4())}/files/path/to/fake/file.txt',
    f'GET/vfs/{str(uuid.uuid4())}/list',
    f'POST/vfs/{str(uuid.uuid4())}/mkdir'
]
ALLOWED_RESULTS_ENDPOINTS = [e for e in ENDPOINTS if 'GET/vfs' in e]
DENIED_TOOL_USE_ENDPOINTS = [
    'DELETE/tools',
    'POST/tools',
    [e for e in ENDPOINTS if 'PUT/tools' in e][0]
]

@pytest.mark.parametrize("endpoint", ENDPOINTS)
@patch('key_authorizer.decode_key')
@patch('key_authorizer.get_policy_from_user')
def test_full_access(mock_get_policy_from_user, mock_decode_key, endpoint):
    """
    Tests the authorizer to make sure that a user with full access can access all the endpoints
    """

    plan = 'FULL'

    api_key = os.environ['ET_ENGINE_API_KEY']
    user_id = os.environ['ET_ENGINE_USER_ID']

    mock_decode_key.return_value = user_id
    mock_get_policy_from_user.return_value = (True, True)

    event = {
        'authorizationToken': api_key,
        'methodArn': ARN_BASE + endpoint,
    }
    context = {}

    response = key_authorizer.handler(event, context, plan=plan)

    assert len(response['policyDocument']['Statement']) == 1
    assert response['policyDocument']['Statement'][0]['Effect'] == 'Allow'
    assert response['policyDocument']['Statement'][0]['Resource'] == [ARN_BASE + endpoint]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@patch('key_authorizer.decode_key')
@patch('key_authorizer.get_policy_from_user')
def test_results_access(mock_get_policy_from_user, mock_decode_key, endpoint):
    """
    Tests the authorizer to make sure that a user with full access can access all the endpoints
    """

    if endpoint in ALLOWED_RESULTS_ENDPOINTS:
        effect = 'Allow'
    else:
        effect = 'Deny'
    

    plan = 'RESULTS'

    api_key = os.environ['ET_ENGINE_API_KEY']
    user_id = os.environ['ET_ENGINE_USER_ID']

    mock_decode_key.return_value = user_id
    mock_get_policy_from_user.return_value = (True, True)

    event = {
        'authorizationToken': api_key,
        'methodArn': ARN_BASE + endpoint,
    }
    context = {}

    response = key_authorizer.handler(event, context, plan=plan)

    assert len(response['policyDocument']['Statement']) == 1
    assert response['policyDocument']['Statement'][0]['Effect'] == effect
    assert response['policyDocument']['Statement'][0]['Resource'] == [ARN_BASE + endpoint]



@pytest.mark.parametrize("endpoint", ENDPOINTS)
@patch('key_authorizer.decode_key')
@patch('key_authorizer.get_policy_from_user')
def test_tool_use_access(mock_get_policy_from_user, mock_decode_key, endpoint):
    """
    Tests the authorizer to make sure that a user with full access can access all the endpoints
    """

    if endpoint in DENIED_TOOL_USE_ENDPOINTS:
        effect = 'Deny'
    else:
        effect = 'Allow'
    

    plan = 'TOOL_USE'

    api_key = os.environ['ET_ENGINE_API_KEY']
    user_id = os.environ['ET_ENGINE_USER_ID']

    mock_decode_key.return_value = user_id
    mock_get_policy_from_user.return_value = (True, True)

    event = {
        'authorizationToken': api_key,
        'methodArn': ARN_BASE + endpoint,
    }
    context = {}

    response = key_authorizer.handler(event, context, plan=plan)

    assert len(response['policyDocument']['Statement']) == 1
    assert response['policyDocument']['Statement'][0]['Effect'] == effect
    assert response['policyDocument']['Statement'][0]['Resource'] == [ARN_BASE + endpoint]
