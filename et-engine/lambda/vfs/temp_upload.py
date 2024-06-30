import json
import boto3

class CompleteStringNotRecognizedError(Exception):
    pass


def handler(event, context):
    """
    https://blog.derlin.ch/aws-s3-multipart-uploads-presigned-urls-vs-federation-tokens
    """

    upload_type = "multipart"
    bucket_name = "temp-data-transfer-bucket-test"

    s3 = boto3.client('s3', region_name="us-east-2")

    print("** UPLOAD REQUESTED **")
    print("event: ", event)
    print("context:", context)

    response = {
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }

    try:
        body = json.loads(event['body'])
        key = body['key']
        print("Request Body:", body)

    except KeyError as e:
        print(f"KeyError when loading request body: {e}")
        response['statusCode'] = 502
        response['body'] = json.dumps("Request missing body or key")
        return response
    
    except Exception as e:
        print(f"Unknown error when loading request body: {e}")
        response['statusCode'] = 501
        response['body'] = json.dumps("Error parsing request")
        return response


    try:
        complete_string = body['complete']

        print("Found complete string: ", complete_string)
        if complete_string == "true":
            print('Complete requested')
            complete = True
        elif complete_string == "false":
            print("Complete explicity denied")
            complete = False
        else:
            raise CompleteStringNotRecognizedError
        
    except KeyError as e:
        print(f"No complete string found, moving ahead with complete=False: ", e)
        complete = False

    except CompleteStringNotRecognizedError as e:
        print(f"Complete String Not Recognized Error: {e}")
        response['statusCode'] = 501
        response['body'] = json.dumps("Invalid query string parameter")
        return response
    
    except Exception as e:
        print(f"Unknown exception occurred while parsing complete string: {e}")
        response['statusCode'] = 501
        response['body'] = json.dumps("Unkown exception occurred")
        return response


    if complete:
        print('Completing multipart upload')
        try:
            parts = body['parts'] # yikes
            upload_id = body['UploadId']

            parts = sorted(parts, key=lambda x: x['PartNumber'])

            s3.complete_multipart_upload(
                Bucket=bucket_name,
                Key=key,
                MultipartUpload={"Parts": parts},
                UploadId=upload_id,
            )
            response['statusCode'] = 200
            return response

        except KeyError as e:
            print(f"KeyError completing multipart upload: {e}")
            response['statusCode'] = 501
            response['body'] = json.dumps("Missing 'parts' or 'UploadId' in request body when completing multipart upload")
            return response
        
        except Exception as e:
            print(f"Unknown error when completing multipart upload: {e}")
            response['statusCode'] = 501
            response['body'] = json.dumps("Unknown error when completing multipart upload"),
            return response
        

    # Create presigned post
    if upload_type == "multipart":
        print('Creating multipart upload')
        try:
            num_parts = body['num_parts']
        
            multipart_upload = s3.create_multipart_upload(Bucket=bucket_name, Key=key)
            upload_id = multipart_upload["UploadId"]
            # Generate the presigned URL for each part
            urls = []
            for part_number in range(1, num_parts + 1): # parts start at 1
                url = s3.generate_presigned_url(
                    ClientMethod="upload_part",
                    Params={
                        "Bucket": bucket_name,
                        "Key": key,
                        "UploadId": upload_id,
                        "PartNumber": part_number,
                    },
                )
                urls.append((part_number, url))


            print('Success')
            print('Number of parts:',len(urls))
            response['statusCode'] = 200
            response['body'] = json.dumps({
                'UploadId': upload_id,
                'urls': urls
            })

            payload = json.dumps({
                'UploadId': upload_id,
                'urls': urls
            })
            print('Size of payload:', len(payload.encode('utf-8')))
            print('RETURNING:', response)
            return response

        except KeyError as e:
            print(f"KeyError when creating multipart upload: {e}")
            response['statusCode'] = 501
            response['body'] = json.dumps("Number of parts not specified properly in request body")
            return response
        
        except Exception as e:
            print(f"Error creating multipart upload: {e}")
            response['statusCode'] = 501
            response['body'] = json.dumps("Error creating multipart upload")
            return response
    else:
        print('Creating single part upload')
        try:
            presigned_post = s3.generate_presigned_post(
                Bucket=bucket_name, 
                Key=key,
                ExpiresIn=3600
            )   
            print('Success')
            response['statusCode'] = 200
            response['body'] = json.dumps(presigned_post)
            return response


        except Exception as e:
            print(f"Error creating upload: {e}")
            response['statusCode'] = 501
            response['body'] = json.dumps("Error generating presigned url")
            return response
            

    
    