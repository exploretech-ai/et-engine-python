from flask import Blueprint, Response, request
import os
import json
import uuid
import shutil
import datetime
import boto3
import asyncio, aiofiles
import random

from . import EFS_MOUNT_POINT, LOGGER, CONNECTION_POOL
from . import utils

vfs = Blueprint('vfs', __name__)


@vfs.route('/vfs', methods=['GET'])
def list_vfs():

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    
    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT name, vfsID FROM VirtualFilesystems WHERE userID = %s
            """,
            (user_id,)
        )
        available_vfs = cursor.fetchall()

        cursor.execute(
            """
            SELECT 
                name, vfsID 
            FROM
                VirtualFileSystems
            INNER JOIN Sharing
                ON VirtualFileSystems.vfsID = Sharing.resourceID AND Sharing.resource_type = 'vfs' AND Sharing.granteeID = %s
            """,
            (user_id,)
        )
        shared_vfs = cursor.fetchall()
        for vfs in available_vfs:
            vfs = vfs + ("owned",)
        for vfs in shared_vfs:
            vfs = vfs + ("shared",)

        available_vfs.extend(shared_vfs)
        
        return Response(json.dumps(available_vfs), status=200)
    
    except:
        return Response("Unknown error", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@vfs.route('/vfs', methods=['POST'])
def create_vfs():

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context["request_id"]

    try:
        request_data = request.get_data(as_text=True)
        body = json.loads(request_data)
        vfs_name = body['name']
    except:
        return Response("Error parsing request", status=400)
    
    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT name FROM VirtualFilesystems WHERE userID = %s
            """,
            (user_id,)
        )
        available_vfs = [row[0] for row in cursor.fetchall()]
        if vfs_name in available_vfs:
            return Response(f"'{vfs_name}' already exists", status=409)
        
        vfs_id = str(uuid.uuid4())
        cfn = boto3.client('cloudformation')
        parameters = utils.vfs_template_parameters(vfs_id)

        cfn.create_stack(
            StackName='vfs-' + vfs_id,
            TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/efs-basic.yaml',
            Parameters=parameters,
            Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
        )

        cursor.execute(
            """
            INSERT INTO VirtualFileSystems (vfsID, userID, name)
            VALUES (%s, %s, %s)
            """,
            (vfs_id, user_id, vfs_name,)
        )
        connection.commit()

        return Response(status=200)
    
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response("Unknown error", status=500)

    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@vfs.route('/vfs/<vfs_id>', methods=['DELETE'])
def delete_vfs(vfs_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context["request_id"]
    is_owned = context['is_owned']

    if not is_owned:
        return Response("Resource not owned", status=403)

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:
        
        cursor.execute(
            """
            DELETE FROM VirtualFilesystems WHERE userID = %s AND vfsID = %s
            """,
            (user_id, vfs_id)
        )
        connection.commit()

        utils.empty_bucket(f"vfs-{vfs_id}")
        utils.delete_stack(f"vfs-{vfs_id}")

        return Response(f"Successfully deleted VFS {vfs_id}", status=200)
    
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response("Unknown error", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@vfs.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['GET'])
def download_file(vfs_id, filepath):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context["request_id"]

    full_file_path = os.path.join(EFS_MOUNT_POINT, vfs_id, filepath)

    if "/../" in full_file_path:
        LOGGER.info(f"[{request_id}] ** ALERT: POTENTIALLY MALICIOUS PATH **")
        return Response("Invalid path", status=403)
    
    if not os.path.exists(full_file_path):
        return Response(f"File '{filepath}' does not exist", status=404)

    def stream_file(file_to_stream):
        with open(file_to_stream, "rb") as file_object:
            while True:
                chunk = file_object.read(8192)
                if not chunk:
                    break
                yield chunk
            
    return Response(stream_file(full_file_path))


# @vfs.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['POST'])
# def upload_file(vfs_id, filepath):

#     context = json.loads(request.environ['context'])
#     user_id = context['user_id']
#     request_id = context['request_id']

#     upload_type = "multipart"
#     bucket_name = "vfs-" + vfs_id

#     s3 = boto3.client('s3', region_name="us-east-2")

#     try:
#         request_data = request.get_data(as_text=True)
#         body = json.loads(request_data)
    
#     except KeyError as e:
#         return Response("Request missing body", status=400)
    
#     except Exception as e:
#         return Response("Error parsing request body", status=400)

#     try:
#         complete_string = body['complete']

#         if complete_string == "true":
#             complete = True

#         elif complete_string == "false":
#             complete = False

#         else:
#             return Response("Invalid 'complete' code, use either 'true' or 'false'", status=400)
        
#     except KeyError as e:
#         # Continue if 'complete' not found in request body
#         complete = False
    
#     except Exception as e:
#         LOGGER.exception(f"[{request_id}]")
#         return Response("Unknown error", status=500)

#     if complete:
#         try:
#             parts = body['parts'] # yikes
#             upload_id = body['UploadId']

#             parts = sorted(parts, key=lambda x: x['PartNumber'])

#             s3.complete_multipart_upload(
#                 Bucket=bucket_name,
#                 Key=filepath,
#                 MultipartUpload={"Parts": parts},
#                 UploadId=upload_id,
#             )
#             return Response(status=200)

#         except KeyError as e:
#             return Response("Missing 'parts' or 'UploadId' in request body when completing multipart upload", status=400)
        
#         except Exception as e:
#               return Response("Unknown error when completing multipart upload", status=500)
        

#     # Create presigned post
#     if upload_type == "multipart":
#         try:
#             num_parts = body['num_parts']
        
#             multipart_upload = s3.create_multipart_upload(Bucket=bucket_name, Key=filepath)
#             upload_id = multipart_upload["UploadId"]

#             urls = []
#             for part_number in range(1, num_parts + 1): # parts start at 1
#                 url = s3.generate_presigned_url(
#                     ClientMethod="upload_part",
#                     Params={
#                         "Bucket": bucket_name,
#                         "Key": filepath,
#                         "UploadId": upload_id,
#                         "PartNumber": part_number,
#                     },
#                 )
#                 urls.append((part_number, url))

#             payload = json.dumps({
#                 'UploadId': upload_id,
#                 'urls': urls
#             })
#             return Response(payload, status=200)

#         except KeyError as e:
#             return Response("Number of parts not specified properly in request body", status=400)
        
#         except Exception as e:
#             return Response("Unknown error while creating multipart upload", status=500)
        
#     else:
#         try:
#             presigned_post = s3.generate_presigned_post(
#                 Bucket=bucket_name, 
#                 Key=filepath,
#                 ExpiresIn=3600
#             )   
#             payload = json.dumps(presigned_post)
#             return Response(payload, status=200)

#         except Exception as e:
#             LOGGER.exception(e)
#             return Response("Error generating presigned url", status=500)


@vfs.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['PUT'])
async def upload_part(vfs_id, filepath):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context["request_id"]

    full_file_path = os.path.join(EFS_MOUNT_POINT, vfs_id, filepath)

    if "/../" in full_file_path:
        LOGGER.info(f"[{request_id}] ** ALERT: POTENTIALLY MALICIOUS PATH **")
        return Response("Invalid path", status=403)

    try:
        data = request.get_data()
        if 'Content-Range' not in request.headers:
            return Response("Missing required Content-Range header")

        content_string = request.headers['Content-Range'].strip()

        chunk_params = content_string.split(":")
        upload_id = chunk_params[0].strip()[1:-1]

        content_range = [int(b) for b in chunk_params[1].split("-")]
        start_bytes = content_range[0]

        expected_chunk_size = content_range[1] - content_range[0]

        if len(data) != expected_chunk_size:
            return Response("Received chunk size does not match Content-Length header", status=400)

        destination = f"{full_file_path}.{upload_id}"

        async with aiofiles.open(destination, "r+b") as f:
            await f.seek(start_bytes, 0)
            await f.write(data)

        return Response(status=200)
    
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response("Unkown error", status=500)
    

@vfs.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['POST'])
def upload(vfs_id, filepath):
    """
    Initialize or complete a multipart upload. Initializations include the size in the request body. Completions include the upload ID and a boolean true/false string in the body.

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns the initialization information if it's an initialization request.
    :status 403: Requested file path forbidden.
    :status 400: Invalid request body.
    :status 500: Unknown error occurred during processing.

    **Request Syntax (Initialize)**:

    .. sourcecode:: json

       {
          "size": 123
       }

    **Request Syntax (Complete)**:

    .. sourcecode:: json

       {
         "complete": "true" | "false"
         "upload_id": "string"
       }

    **Response Syntax (Initialize)**:

    .. sourcecode:: json

       [
         {
           "upload_id": "string"
         }
       ]

    :raises: May raise exceptions related to database operations or service availability.
    """
    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    request_id = context["request_id"]

    full_file_path = os.path.join(EFS_MOUNT_POINT, vfs_id, filepath)

    if "/../" in full_file_path:
        LOGGER.info(f"[{request_id}] ** ALERT: POTENTIALLY MALICIOUS PATH **")
        return Response("Invalid path", status=403)

    try:
        body = request.get_data(as_text=True)
        body = json.loads(body)

        if 'complete' in body and body['complete']:
            if 'upload_id' not in body:
                return Response("upload_id is required to complete the upload", status=400)
            upload_id = body['upload_id']
            destination = f"{full_file_path}.{upload_id}"
            os.rename(destination, full_file_path)
            return Response(status=200)

        if 'size' not in body:
            return Response("Invalid request body", status=400)
        
        file_size_bytes = body['size']
        sample_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        upload_id = ''.join(random.choices(sample_str, k = 20))  

        destination = f"{full_file_path}.{upload_id}"
        
        with open(destination, "wb") as f:
            f.seek(file_size_bytes - 1)
            f.write(b'\0')
    
        payload = json.dumps({
            'upload_id': upload_id
        })
      
        return Response(payload, status=200)
    
    except Exception as e:
        LOGGER.exception(f"[{request_id}]")
        return Response("Unkown error", status=500)


@vfs.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['DELETE'])
def delete_file(vfs_id, filepath):

    full_path = os.path.join(EFS_MOUNT_POINT, vfs_id, filepath)
    if "/../" in full_path:
        LOGGER.info(f"** ALERT: POTENTIALLY MALICIOUS PATH **")
        return Response("Invalid path", status=403)
    
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            return Response('Path is neither file nor directory', status=400)
        
    except OSError:
        return Response("File delete failed", status=400)
    
    else:
        return Response(status=200)


@vfs.route('/vfs/<vfs_id>/mkdir/<path:filepath>', methods=['POST'])
def make_directory(vfs_id, filepath):

    context = json.loads(request.environ['context'])
    request_id = context["request_id"]
    
    full_path = os.path.join(EFS_MOUNT_POINT, vfs_id, filepath)
    if "/../" in full_path:
        LOGGER.warning(f"[{request_id}] ** ALERT: POTENTIALLY MALICIOUS PATH **")
        return Response("Invalid path", status=403)
    
    try:
        os.mkdir(full_path)

    except FileExistsError:
        return Response("Directory already exists", status=409)
    
    except FileNotFoundError:
        return Response("Parent directory does not exist", status=400)
    
    except Exception:
        LOGGER.exception(f"[{request_id}]")
        return Response("Unknown error while creating directory", status=500)
    
    else:
        return Response(status=200)

    
@vfs.route('/vfs/<vfs_id>/list', methods=['GET'], strict_slashes=False)
@vfs.route('/vfs/<vfs_id>/list/<path:filepath>', methods=['GET'])
def list_directory(vfs_id, filepath=""):

    full_path = os.path.join(EFS_MOUNT_POINT, vfs_id, filepath)

    if "/../" in full_path:
        LOGGER.info(f"** ALERT: POTENTIALLY MALICIOUS PATH **")
        return Response("Invalid path", status=403)
    
    try:
        dir_items = []
        file_items = []
        for (dirpath, dirnames, filenames) in os.walk(full_path):
            dir_items.extend(dirnames)
            file_items.extend(filenames)
            break

    except Exception as error:
        return Response("Unable to list files", status=500)
    
    payload = json.dumps({
        'directories': dir_items,
        'files': file_items
    })

    return Response(payload, status=200)


@vfs.route('/vfs/<vfs_id>/share', methods=['POST'])
def share_filesystem(vfs_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    is_owned = context['is_owned']

    if not is_owned:
        return Response("Must be owner to share", status=403)

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
            "SELECT * FROM Sharing WHERE ownerID = %s AND granteeID = %s AND resource_type = %s AND resourceId = %s",
            (user_id, grantee_id, "vfs", vfs_id)
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
                "vfs", 
                vfs_id, 
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