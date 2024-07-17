from flask import Blueprint, Response, request
import json
import datetime
import boto3
from . import utils, CONNECTION_POOL, LOGGER

tasks = Blueprint('tasks', __name__)


@tasks.route('/tasks', methods=['GET'])
def list_tasks():
    
    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            SELECT taskID, toolID, logID, start_time, hardware, args, status, status_time, exit_code, exit_reason FROM Tasks WHERE userID = %s
            """,
            (user_id,)
        )
        task_list = cursor.fetchall()
        tasks = []
        for row in task_list:

            tool_id = row[1]

            # NOTE: Could probably replace this with a join outside of the for loop for better performance
            cursor.execute(
                """
                SELECT name FROM Tools WHERE toolID = %s
                """,
                (tool_id,)
            )
            tool_name = cursor.fetchone()[0]
            tasks.append({
                'taskID':       row[0],
                'toolName':     tool_name,
                'logID':        row[2],
                'startTime':    row[3].strftime('%Y-%m-%d %H:%M:%S'),
                'hardware':     row[4],
                'args':         row[5],
                'status':       row[6],
                'statusTime':   row[7].strftime('%Y-%m-%d %H:%M:%S'),
                'exitCode':     row[8],
                'exitReason':   row[9]
            })

        payload = json.dumps(tasks)
        return Response(payload, status=200)
    
    except:
        return Response("Unknown error occurred", status=500)
    
    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)


@tasks.route('/tasks', methods=['DELETE'])
def clear_tasks():

    context = json.loads(request.environ['context'])
    user_id = context['user_id']

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            DELETE FROM Tasks WHERE userID = %s
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


@tasks.route('/tasks/<task_id>', methods=['GET'])
def describe_task(task_id):

    context = json.loads(request.environ['context'])
    user_id = context['user_id']
    
    engine_stack_outputs = utils.get_stack_outputs('ETEngine')
    cluster_name = utils.get_component_from_outputs(engine_stack_outputs, "ClusterName")

    connection = CONNECTION_POOL.getconn()
    cursor = connection.cursor()
    try: 
        cursor.execute(
            """
            SELECT taskArn FROM Tasks WHERE userID = %s AND taskID = %s
            """,
            (user_id, task_id)
        )
        if cursor.rowcount == 0:
            return Response("Task does not exist", status=404)
        
        task_arn = cursor.fetchone()[0]

    except Exception as e:
        
        connection = CONNECTION_POOL.getconn()
        cursor = connection.cursor()

        request_id = context["request_id"]
        LOGGER.exception(f"[{request_id}]")
        return Response("Unknown error occurred", status=500)
    
    try:     

        exit_code = -1
        exit_reason = None

        ecs = boto3.client('ecs')
        task_description = ecs.describe_tasks(cluster=cluster_name, tasks=[task_arn])
        task = task_description['tasks'][0]
        task_status = task['lastStatus']

    except IndexError:
        payload = json.dumps({
            'status': 'STOPPED',
            'code': 2,
            'reason': 'task expired'
        })
        return Response(payload, status=200)
    
    try:
        
        container_list = task['containers']
        container = container_list[0]

        if 'exitCode' in container:
            exit_code = container['exitCode']
        if 'reason' in container:
            exit_reason = container['reason']

        status_time = datetime.datetime.now()
        status_time = status_time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            """
            UPDATE Tasks SET status = %s, status_time = %s, exit_code = %s, exit_reason = %s WHERE userID= %s AND taskID = %s
            """,
            (task_status, status_time, exit_code, exit_reason, user_id, task_id)
        )
        connection.commit()

    except KeyError as e:
        pass

    except IndexError as e:
        pass

    except Exception as e:
        request_id = context["request_id"]
        LOGGER.exception(f"[{request_id}]")
        return Response("Unknown error occurred", status=500)

    finally:
        cursor.close()
        CONNECTION_POOL.putconn(connection)
        
    payload = json.dumps({
        'status': task_status,
        'code': exit_code,
        'reason': exit_reason
    })
    return Response(payload, status=200)
    
    
    
    

    
