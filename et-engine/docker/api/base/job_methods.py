from flask import Blueprint, Response, request
import json
import datetime
import boto3
from botocore.exceptions import ClientError

from . import utils, CONNECTION_POOL, LOGGER

jobs = Blueprint('jobs', __name__)


@jobs.route('/batches', methods=['GET'])
def list_batches():
    """
    List all the available batches for the user

    The user is identified by the 'user_id' in the request context.

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns a list of batch id's and associated properties.
    :status 500: Unknown error occurred during processing.

    **Response Syntax**:

    .. sourcecode:: json

       [
         {
           "batch_id": "string",
           "tool_id": "string",
           "n_jobs": 123,
           "hardware": {
             "filesystems": [
               "id"
             ],
             "cpu" 123,
             "memory": 123
           }
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
            SELECT * FROM Batches WHERE userID = %s
            """,
            (user_id,)
        )
        rows = cursor.fetchall()

        batches = []
        for r in rows:
            batches.append({
                "batch_id": r[0],
                "tool_id":  r[2],
                "n_jobs":   r[4],
                "hardware": r[3]
            })

        payload = json.dumps(batches)
        return Response(payload, status=200)
    
    except Exception as e:
        LOGGER.exception(e)
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@jobs.route('/batches', methods=['DELETE'])
def clear_batches():
    """
    Deletes all the available batches and jobs for the user

    The user is identified by the 'user_id' in the request context.

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. No return text.
    :status 500: Unknown error occurred during processing.

    :raises: May raise exceptions related to database operations or service availability.
    """

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        
        cursor.execute(
            """
            DELETE 
            FROM Jobs
            USING Batches
            WHERE Batches.userID = %s AND Jobs.batchID = Batches.batchID
            """,
            (user_id,)
        )

        cursor.execute(
            """
            DELETE FROM Batches WHERE userID = %s
            """,
            (user_id,)
        )
        connection.commit()
        return Response(status=200)
    
    except:
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@jobs.route('/batches/<batch_id>', methods=['GET'])
def describe_batch(batch_id):
    """
    Returns attributes for batch

    The user is identified by the 'user_id' in the request context.

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns a list of batch id's and associated properties.
    :status 500: Unknown error occurred during processing.

    **Response Syntax**:

    .. sourcecode:: json

       [
         {
           "batch_id": "string",
           "tool_id": "string",
           "n_jobs": 
           "hardware": {
             "filesystems": [
               "id"
             ],
             "memory": 123,
             "cpu": 123
           },
           "n_submitted": 123,
           "submitted_jobs": [         # optional
             {
               "": ""
             }
           ]
         }
       ]

    :raises: May raise exceptions related to database operations or service availability.
    """

    batch_client = boto3.client('batch')

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 

        cursor.execute(
            """
            SELECT toolID, n_jobs, hardware FROM Batches WHERE batchID = %s
            """,
            (batch_id,)
        )
        row = cursor.fetchall()[0]

        batch_info = {
            "batch_id": batch_id,
            "tool_id": row[0],
            "n_jobs": row[1],
            "hardware": row[2]
        }

        cursor.execute(
            """
            SELECT jobID FROM Jobs WHERE batchID = %s
            """,
            (batch_id,)
        )
        rows = cursor.fetchall()
        job_ids = [r[0] for r in rows]

        batch_info['n_submitted'] = len(job_ids)

        if batch_info['n_submitted'] == 0:
            payload = json.dumps(batch_info)
            return Response(payload, status=200)
        
        submitted_jobs = {
            'SUBMITTED': 0, 
            'PENDING': 0, 
            'RUNNABLE': 0, 
            'STARTING': 0,
            'RUNNING': 0, 
            'SUCCEEDED': 0,
            'FAILED': 0
        }

        for job_chunk in chunks(job_ids, 100):
            
            job_descriptions = batch_client.describe_jobs(
                jobs=job_chunk
            )
            
            for description in job_descriptions['jobs']:
                job_info = {
                    'job_id': description['jobId']
                }
                status = description['status']
                submitted_jobs[status] += 1
                
        batch_info['submitted_jobs'] = submitted_jobs

        payload = json.dumps(batch_info)
        return Response(payload, status=200)
    
    except Exception as e:
        LOGGER.exception(e)
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)
    

@jobs.route('/batches/<batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """
    Deletes the specified batch

    The user is identified by the 'user_id' in the request context.

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. No return text.
    :status 500: Unknown error occurred during processing.

    :raises: May raise exceptions related to database operations or service availability.
    """

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        
        cursor.execute(
            """
            DELETE FROM Jobs WHERE batchID = %s
            """,
            (batch_id,)
        )

        cursor.execute(
            """
            DELETE FROM Batches WHERE userID = %s AND batchID = %s
            """,
            (user_id, batch_id)
        )
        connection.commit()
        return Response(status=200)
    
    except:
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@jobs.route('/batches/<batch_id>/jobs', methods=['GET'])
def list_jobs(batch_id):
    """
    List all the available jobs in the user's requested batch

    The user is identified by the 'user_id' in the request context.

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns a list of batch id's and associated properties.
    :status 500: Unknown error occurred during processing.

    **Response Syntax**:

    .. sourcecode:: json

       [
         {
           "job_id": "string",
           "log_id": "string",
           "args": {
             "name": "value"
           }
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
            SELECT jobID, logID, args FROM Jobs WHERE batchID = %s
            """,
            (batch_id,)
        )
        rows = cursor.fetchall()

        jobs = []
        for r in rows:
            jobs.append({
                "job_id": r[0],
                "log_id": r[1],
                "args":   r[2]
            })

        payload = json.dumps(jobs)
        return Response(payload, status=200)
    
    except Exception as e:
        LOGGER.exception(e)
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)

    
@jobs.route('/batches/<batch_id>/jobs/<job_id>', methods=['GET'])
def describe_job(batch_id, job_id):
    """
    Returns attributes for the specific job

    The user is identified by the 'user_id' in the request context.

    :reqheader Authorization: API key or Bearer token for user authentication
    :status 200: Success. Returns a list of batch id's and associated properties.
    :status 500: Unknown error occurred during processing.

    **Response Syntax**:

    .. sourcecode:: json

       [
         {
           "job_id": "string",
           "log_id": "string",
           "hardware": {
             "filesystems": [
               "id"
             ],
             "memory": 123,
             "cpu": 123
           },
           "args": {
             "name": "value"
           },
           "status": "string",
           "reason": "string",
           "create_time": "string",
           "start_time": "string",
           "stop_time": "string",
         }
       ]

    :raises: May raise exceptions related to database operations or service availability.
    """

    batch_client = boto3.client('batch')

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            SELECT logID, args FROM Jobs WHERE jobID = %s
            """,
            (job_id,)
        )
        row = cursor.fetchall()[0]

        job_info = {
            "job_id": job_id,
            "log_id": row[0],
            "args":   row[1]
        }

        cursor.execute(
            """
            SELECT toolID, hardware FROM Batches WHERE batchID = %s
            """,
            (batch_id,)
        )
        row = cursor.fetchall()[0]
        job_info['tool_id'] = row[0]
        job_info['hardware'] = row[1]


        job_description = batch_client.describe_jobs(
            jobs=[
                job_id
            ]
        )
        LOGGER.info(job_description)

        # Defaults
        job_info['status'] = "SUBMITTING"
        job_info['reason'] = ""
        job_info['create_time'] = ""
        job_info['start_time'] = ""
        job_info['stop_time'] = ""

        if 'jobs' not in job_description or len(job_description['jobs']) > 0:
            payload = json.dumps(job_info)
            return Response(payload, status=200)
        

        job_description = job_description['jobs'][0]
        job_info['status'] = job_description['status']
        job_info['create_time'] = job_description['createdAt']

        if 'statusReason' in job_description:
            job_info['reason'] = job_description['statusReason']

        if 'startedAt' in job_description:
            job_info['start_time'] = job_description['startedAt']

        if 'stoppedAt' in job_description:
            job_info['stop_time'] = job_description['stoppedAt']

        payload = json.dumps(job_info)
        return Response(payload, status=200)
    
    except Exception as e:
        LOGGER.exception(e)
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

 
