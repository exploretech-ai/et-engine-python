from flask import Blueprint, Response, request
import os
import json
import uuid
import shutil
import datetime
import boto3
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
            SELECT name, vfs_id FROM VirtualFilesystems WHERE userID = %s
            """,
            (user_id,)
        )
        available_vfs = cursor.fetchall()

        cursor.execute(
            """
            SELECT 
                name, vfs_id 
            FROM
                VirtualFileSystems
            INNER JOIN Sharing
                ON VirtualFileSystems.vfs_id = Sharing.resourceID AND Sharing.resource_type = 'vfs' AND Sharing.granteeID = %s
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
            (user_id)
        )
        available_vfs = [row[0] for row in cursor.fetchall()]
        if vfs_name in available_vfs:
            return Response(f"'{vfs_name}' already exists", status=409)
        
        vfs_id = str(uuid.uuid4())
        cfn = boto3.client('cloudformation')
        parameters = utils.vfs_template_parameters(vfs_id)
        print("VFS ID:", vfs_id)
        print("Stack Parameters:", parameters)
        
        cfn.create_stack(
            StackName='vfs-' + vfs_id,
            TemplateURL='https://et-engine-templates.s3.us-east-2.amazonaws.com/efs-basic.yaml',
            Parameters=parameters,
            Capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
        )

        cursor.execute(
            """
            INSERT INTO VirtualFileSystems (vfs_id, userID, name)
            VALUES (%s, %s, %s)
            """,
            (vfs_id, user_id, vfs_name,)
        )
        connection.commit()

        return Response(f"'{vfs_name}' successfully created", status=200)
    
    except:
        return Response("Unknown error", status=500)

    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@vfs.route('/vfs/<vfs_id>', methods=['DELETE'])
def delete_vfs(vfs_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    is_owned = context['is_owned']

    if not is_owned:
        return Response("Resource not owned", status=403)

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:
        
        cursor.execute(
            """
            DELETE FROM VirtualFilesystems WHERE userID = %s AND vfs_id = %s
            """,
            (user_id, vfs_id)
        )
        connection.commit()

        utils.empty_bucket(f"vfs-{vfs_id}")
        utils.delete_stack(f"vfs-{vfs_id}")

        return Response(f"Successfully deleted VFS {vfs_id}", status=200)
    
    except:
        return Response("Unknown error", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@vfs.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['GET'])
def download_file(vfs_id, filepath):

    LOGGER.info(f"VFS: {vfs_id}, File: {filepath}")

    full_file_path = os.path.join(EFS_MOUNT_POINT, vfs_id, filepath)

    if "/../" in full_file_path:
        LOGGER.info(f"** ALERT: POTENTIALLY MALICIOUS PATH **")
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


@vfs.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['POST'])
def upload_file(vfs_id, filepath):

    upload_type = "multipart"
    bucket_name = "vfs-" + vfs_id

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
        return Response("Unknown error while parsing checking for a 'complete' string", status=500)

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
        print('Creating single part upload')
        try:
            presigned_post = s3.generate_presigned_post(
                Bucket=bucket_name, 
                Key=filepath,
                ExpiresIn=3600
            )   
            payload = json.dumps(presigned_post)
            return Response(payload, status=200)

        except Exception as e:
            return Response("Error generating presigned url", status=500)


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


@vfs.route('/vfs/<vfs_id>/files/<path:filepath>', methods=['PUT'])
def make_directory(vfs_id, filepath):
    
    full_path = os.path.join(EFS_MOUNT_POINT, vfs_id, filepath)
    if "/../" in full_path:
        LOGGER.info(f"** ALERT: POTENTIALLY MALICIOUS PATH **")
        return Response("Invalid path", status=403)
    
    try:
        os.mkdir(full_path)

    except FileExistsError:
        return Response("Directory already exists", status=409)
    
    except FileNotFoundError:
        return Response("Parent directory does not exist", status=400)
    
    except Exception:
        return Response("Unknown error while creating directory", status=500)
    
    else:
        return Response(status=200)

    
@vfs.route('/vfs/<vfs_id>/list', methods=['GET'])
def list_root_directory(vfs_id):

    full_path = os.path.join(EFS_MOUNT_POINT, vfs_id)

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


@vfs.route('/vfs/<vfs_id>/list/<path:filepath>', methods=['GET'])
def list_directory(vfs_id, filepath):

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
    
    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try:       
        if 'grantee' in body:
            grantee_id = body['grantee']
        else:
            return Response('Request body has no grantee', status=400)

        # throws an error if poorly-formed UUID
        uuid.UUID(grantee_id, version=4)
        print('Grantee ID formatted properly')
        
        accessID = str(uuid.uuid4())
        date_created = datetime.datetime.now()
        date_created = date_created.strftime('%Y-%m-%d %H:%M:%S')

        if user_id == grantee_id:
            return Response("Cannot share with yourself", status=403)
        
        query = "SELECT * FROM Sharing WHERE ownerID = %s AND granteeID = %s AND resource_type = %s AND resourceId = %s"
        cursor.execute(query, (user_id, grantee_id, "vfs", vfs_id))
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
        print('INVALID GRANTEE ID: must be uuid4', e)
        return Response("Invalid grantee", status=400)
        
    except Exception as e:
        return Response("Unknown error", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)