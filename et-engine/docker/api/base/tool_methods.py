from flask import Blueprint, Response, request
import json
import uuid
import datetime
import time
import boto3
from . import utils
from . import CONNECTION_POOL, LOGGER, JOB_SUBMISSION_QUEUE_URL


class InvalidRequestBodyError(Exception):
    pass


tools = Blueprint('tools', __name__)


@tools.route('/tools', methods=['GET'])
def list_tools():
    """
    Lists available tools for the user

    :reqheader Authorization: API key or Bearer token for user authentication

    **Response Syntax**:
    NOTE: the JSON below is actually returned as a 2D list not a list of maps

    .. sourcecode:: json

       [
         {
           "name": "string",
           "toolId": "string",
           "isOwned": "true" | "false"
         }
       ]


    :raises: May raise exceptions related to database operations or service availability.
    """
    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            SELECT name, toolID FROM Tools WHERE userID = %s
            """,
            (user_id,)
        )
        available_tools = cursor.fetchall()

        cursor.execute(
            """
            SELECT 
                name, toolID 
            FROM
                Tools
            INNER JOIN Sharing
                ON Tools.toolID = Sharing.resourceID AND Sharing.resource_type = 'tools' AND Sharing.granteeID = %s
            """,
            (user_id,)
        )
        shared_tools = cursor.fetchall()

        for tool in available_tools:
            tool = tool + ("owned",)
        for tool in shared_tools:
            tool = tool + ("shared",)

        available_tools.extend(shared_tools)
        payload = json.dumps(available_tools)
        return Response(payload, status=200)

    except:
        return Response("Unknown error occurred", status=500)

    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)

    
@tools.route('/tools', methods=['POST'])
def create_tool():
    """
    Creates a new tool (NOTE ARGS ARE NOT IMPLEMENTED YET)

    :reqheader Authorization: API key or Bearer token for user authentication

    **Request Syntax**:

    .. sourcecode:: json

       {
          "name": "string",
          "description": "string",
          "args": [
            {
              "name": "string",
              "config": {
                "type": "string",
                "required": "true" | "false",
                "description": "string",
                "default": value
              }
            } 
          ]
       }

    ** Argument Types **

    +--------+-------------+
    | Type   | Renders As  |
    +========+=============+
    | string | text box    |
    +--------+-------------+
    | int    | text box    |
    +--------+-------------+
    | float  | text box    |
    +--------+-------------+
    | bool   | check box   |
    +--------+-------------+
    | file   | file dialog |
    +--------+-------------+

    :raises: May raise exceptions related to database operations or service availability.
    """

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)

    except Exception as e:
        return Response("Error parsing request body", status=400)

    try:
        tool_name = body['name']
        tool_description = body['description']
    
    except KeyError as e:
        return Response("Request missing name or description", status=400)
    
    except Exception as e:
        return Response("Error parsing request body", status=400)

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            SELECT name FROM Tools WHERE userID = %s
            """,
            (user_id,)
        )
        available_tools = [row[0] for row in cursor.fetchall()]

        if tool_name in available_tools:
            return Response(f"Failed: '{tool_name}' already exists", status=409)
        
        tool_id = str(uuid.uuid4())
        cfn = boto3.client('cloudformation')

        parameters = [
            {
                'ParameterKey': 'toolID',
                'ParameterValue': tool_id
            },
        ]
        
        cfn.create_stack(
            StackName='tool-' + tool_id,
            TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/compute-basic.yaml',
            Parameters=parameters,
            Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
        )

        cursor.execute(
            """
            INSERT INTO Tools (toolID, userID, name, description)
            VALUES (%s, %s, %s, %s)
            """,
            (tool_id, user_id, tool_name, tool_description)
        )
        connection.commit()
        return Response(status=200)
        
    except:
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@tools.route('/tools/<tool_id>', methods=['GET'])
def describe_tool(tool_id):
    """
    Describes the tool

    
    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns a list of batch id's and associated properties.
    :status 500: Unknown error occurred during processing.

    **Request Syntax**:

    {
      "ready": "true" | "false",
      "buildStatus": "string",
      "args": [
        {
          "name": "string",
          "config": {
            "type": "string",
            "required": "true" | "false",
            "description": "string",
            "default": value
          }
        } 
      ]

    ** NOTE **
    Arguments are not yet implemented

    """

    try:
        tool_is_ready = utils.check_ecr(tool_id)
        build_status = utils.check_codebuild(tool_id)
        tool_parameters = json.dumps({
            'ready': tool_is_ready,
            'buildStatus': build_status
        })
        return Response(tool_parameters, status=200)
    
    except:
        return Response("Unknown error occurred", status=500)        


@tools.route('/tools/<tool_id>', methods=['POST'])
def execute_tool(tool_id):
    """
    Submits a job or batch of jobs to the tool execution service

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns the job id(s).
    :status 500: Unknown error occurred during processing.

    **Request Syntax**:

    .. sourcecode:: json

       {
          "fixed_args": {
            "name": {
              "value": <ANY>,
              "type" "string"
            }
          },
          "variable_args: [
            {
              "name": {
                "value": <ANY>,
                "type" "string"
              }
            }
          ],
          "hardware": {
            "filesystems": [
              "id"
            ],
            "memory": 123,
            "cpu": 123
          }
       }

    **Response Syntax**:

    .. sourcecode:: json

       [
         {
           "job_id": "string"
         }
       ]

    :raises: May raise exceptions related to database operations or service availability.
    """

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context['request_id']
    
    try:
        body_string = request.get_data(as_text=True)
        body = json.loads(body_string)
    except json.JSONDecodeError:
        return Response("Invalid JSON in request body", status=400)
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response('Unknown error occurred', status=500)
    
    try:
        body_is_valid = validate_body(body)
        if not body_is_valid:
            raise InvalidRequestBodyError("Invalid request body")       
    except (TypeError, InvalidRequestBodyError) as e:
        return Response("Invalid request body", status=400)
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response('Unknown error occurred', status=500)
    
    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:
        body['submission'] = {
            'user_id': user_id,
            'batch_id': request_id,
            'tool_id': tool_id
        }

        cursor.execute(
            """
            INSERT INTO Batches (batchID, userID, toolID, hardware, n_jobs)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (request_id, user_id, tool_id, json.dumps(body["hardware"]), max(1, len(body["variable_args"])))
        )
        connection.commit()
        
        sqs = boto3.client('sqs')
        sqs.send_message(
            QueueUrl=JOB_SUBMISSION_QUEUE_URL,
            MessageBody=json.dumps(body),
            MessageGroupId=str(uuid.uuid4()),
            MessageDeduplicationId=str(uuid.uuid4())
        )

        return Response(request_id, status=200)
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response('Failed to submit batch', status=500)
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)

    
@tools.route('/tools/<tool_id>', methods=['PUT'])
def push_tool_multipart(tool_id):
    """
    Updates the tool code

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns a list of batch id's and associated properties.
    :status 500: Unknown error occurred during processing.

    **Request Syntax**:

    .. sourcecode:: json

       {
         "num_parts": 123,
         "complete": "true" | "false",
         "parts": [
            *from presigned urls*
         ],
         "UploadId": "string"
       }

    **Response Syntax**:

    .. sourcecode:: json

       {
         "UploadId": "string"
         "urls": [
           "string"
         ]
       }

    :raises: May raise exceptions related to database operations or service availability.
    """

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context['request_id']

    upload_type = "multipart"
    bucket_name = "tool-" + tool_id
    filepath = "tool.tar.gz"

    s3 = boto3.client('s3', region_name="us-east-2")

    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)
    
    except KeyError as e:
        return Response("Request missing body", status=400)
    
    except Exception as e:
        return Response("Error parsing request body", status=400)

    try:
        complete_string = body['complete']

        if complete_string == "true":
            complete = True

        elif complete_string == "false":
            complete = False

        else:
            return Response("Invalid 'complete' code, use either 'true' or 'false'", status=400)
        
    except KeyError as e:
        # Continue if 'complete' not found in request body
        complete = False
    
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response("Unknown error", status=500)

    if complete:
        try:
            parts = body['parts'] # yikes
            upload_id = body['UploadId']

            parts = sorted(parts, key=lambda x: x['PartNumber'])

            s3.complete_multipart_upload(
                Bucket=bucket_name,
                Key=filepath,
                MultipartUpload={"Parts": parts},
                UploadId=upload_id,
            )
            return Response(status=200)

        except KeyError as e:
            return Response("Missing 'parts' or 'UploadId' in request body when completing multipart upload", status=400)
        
        except Exception as e:
              return Response("Unknown error when completing multipart upload", status=500)
        

    # Create presigned post
    if upload_type == "multipart":
        try:
            num_parts = body['num_parts']
        
            multipart_upload = s3.create_multipart_upload(Bucket=bucket_name, Key=filepath)
            upload_id = multipart_upload["UploadId"]

            urls = []
            for part_number in range(1, num_parts + 1): # parts start at 1
                url = s3.generate_presigned_url(
                    ClientMethod="upload_part",
                    Params={
                        "Bucket": bucket_name,
                        "Key": filepath,
                        "UploadId": upload_id,
                        "PartNumber": part_number,
                    },
                )
                urls.append((part_number, url))

            payload = json.dumps({
                'UploadId': upload_id,
                'urls': urls
            })
            return Response(payload, status=200)

        except KeyError as e:
            return Response("Number of parts not specified properly in request body", status=400)
        
        except Exception as e:
            return Response("Unknown error while creating multipart upload", status=500)
        
    else:
        try:
            presigned_post = s3.generate_presigned_post(
                Bucket=bucket_name, 
                Key=filepath,
                ExpiresIn=3600
            )   
            payload = json.dumps(presigned_post)
            return Response(payload, status=200)

        except Exception as e:
            LOGGER.exception(e)
            return Response("Error generating presigned url", status=500)


@tools.route('/tools/<tool_id>', methods=['PATCH'])
def update_args(tool_id):
    """
    Updates the tool arguments (NOT YET IMPLEMENTED)

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns a list of batch id's and associated properties.
    :status 500: Unknown error occurred during processing.

    **Request Syntax**:

    .. sourcecode:: json

       [
         {
           "name": "string",
           "config": {
             "type": "string",
             "required": "true" | "false",
             "description": "string",
             "default": value
           }
         } 
       ]

    :raises: May raise exceptions related to database operations or service availability.
    """
    pass


@tools.route('/tools/<tool_id>', methods=['DELETE'])
def delete_tool(tool_id):
    
    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    is_owned = context['is_owned']

    if not is_owned:
        return Response('Must be owner to delete', status=403)

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            DELETE FROM Tools WHERE userID = %s AND toolID = %s
            """,
            (user_id, tool_id)
        )
        
        utils.empty_bucket("tool-"+tool_id)
        utils.delete_repository("tool-"+tool_id)
        utils.delete_stack("tool-"+tool_id)
        connection.commit()

        return Response(status=200)
    
    except:
        return Response("Unknown error occurred", status=500)

    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@tools.route('/tools/<tool_id>/share', methods=['POST'])
def share_tool(tool_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    is_owned = context['is_owned']

    if not is_owned:
        return Response('Must be owner to share', status=403)
    
    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)
    
    except KeyError as e:
        return Response("Request missing body", status=400)

    except Exception as e:
        return Response("Error parsing request body", status=400)
    
    if 'grantee' in body:
        grantee_id = body['grantee']
    else:
        return Response('Request body has no grantee', status=400)


    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:
        
        # throws an error if poorly-formed UUID
        uuid.UUID(grantee_id, version=4)
        
        accessID = str(uuid.uuid4())
        date_created = datetime.datetime.now()
        date_created = date_created.strftime('%Y-%m-%d %H:%M:%S')

        if user_id == grantee_id:
            return Response("Cannot share with yourself", status=403)
        
        cursor.execute(
            "SELECT * FROM Sharing WHERE ownerID = %s AND granteeID = %s AND resource_type = %s AND resourceID = %s",
            (user_id, grantee_id, "tools", tool_id)
        )
        if cursor.rowcount > 0:
            return Response("Already shared with this user", status=409)
        
        cursor.execute(
            """
            INSERT INTO Sharing (accessID, ownerID, granteeID, resource_type, resourceID, date_granted)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, 
            (
                accessID, 
                user_id, 
                grantee_id, 
                "tools", 
                tool_id, 
                date_created,
            )
        )
        connection.commit()

        return Response(status=200)

    except ValueError as e:
        return Response("Invalid grantee", status=400)
        
    except Exception as e:
        return Response("Unknown error", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


def validate_body(body):
    
    if "hardware" not in body:
        return False

    if not all(key in body["hardware"] for key in ["filesystems", "memory", "cpu"]):
        return False
    
    if "variable_args" not in body:
        return False
    
    if "fixed_args" not in body:
        return False
    
    return True


def fetch_available_vfs(user, cursor):
                    
    query = f"""
        SELECT name, vfsID FROM VirtualFilesystems WHERE userID = '{user}'
    """

    cursor.execute(query)
    available_vfs = cursor.fetchall()

    query = """
        SELECT 
            name, vfsID 
        FROM
            VirtualFileSystems
        INNER JOIN Sharing
            ON VirtualFileSystems.vfsID = Sharing.resourceID AND Sharing.resource_type = 'vfs' AND Sharing.granteeID = %s
    """
    cursor.execute(query, (user,))
    shared_vfs = cursor.fetchall()

    available_vfs.extend(shared_vfs)

    vfs_id_map = {}
    for row in available_vfs:
        vfs_id_map[row[0]] = row[1]

    return vfs_id_map


def log_task(task_arn, user_id, tool_id, log_id, hardware, args, cursor):

    start_time = datetime.datetime.now()
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    status="SUBMITTED"
    status_time = datetime.datetime.now()
    status_time = status_time.strftime('%Y-%m-%d %H:%M:%S')

    task_id = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO Tasks (taskID, taskArn, userID, toolID, logID, start_time, hardware, status, status_time, args)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        task_id,
        task_arn,
        user_id,
        tool_id,
        log_id,
        start_time,
        hardware,
        status,
        status_time,
        args
    ))

    return task_id
    