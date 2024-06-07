import json
import boto3
import db
import datetime

def fetch_status(task_arn):
    print('Fetching status...')
    ecs = boto3.client('ecs')
    task_description = ecs.describe_tasks(
        cluster="ETEngineAPI706397EC-ClusterEB0386A7-M0TrrRi5C32N",
        tasks=[
            task_arn
        ]
    )
    print('Task description: ', task_description)
    
    task = task_description['tasks'][0]
    print('Task: ', task)

    task_status = task['lastStatus']
    print('Status: ', task_status)

    exit_code = -1
    reason = None
    try: 
        print('Fetching exit code...')
        container_list = task['containers']
        print('Container list: ', container_list)
        container = container_list[0]
        print('Container: ', container)

        try: 
            exit_code = container['exitCode']
            print('Found exit code: ', exit_code)
        except KeyError as e:
            print('Key Error while fetching exit code:', e)
            print('proceeding with unknown exit code')
        
        try:
            reason = container["reason"]
            print('Found exit reason:', reason)
        except KeyError as e:
            print('Key Error while fetching exit reason:', e)
            print('proceeding with unknown exit code')

        
    except KeyError as e:
        print('Key Error while processing status:', e)
    except IndexError as e:
        print('Index Error while processing status:', e)

    return {
        'status': task_status,
        'code': exit_code,
        'reason': reason
    }


def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:
        user = event['requestContext']['authorizer']['userID']
        task_id = event['pathParameters']['taskID']

        print(f'User {user} requested status on task {task_id}')

        cursor.execute(f"""
            SELECT taskArn FROM Tasks WHERE userID = '{user}' AND taskID = '{task_id}'
        """)
        task_arn = cursor.fetchone()[0]
        print('Found task ARN: ', task_arn)

        status = fetch_status(task_arn)
        
        status_time = datetime.datetime.now()
        status_time = status_time.strftime('%Y-%m-%d %H:%M:%S')
        print('Status update time: ', status_time)

        task_status = status["status"]
        exit_code = status["code"]
        exit_reason = status["reason"]

        cursor.execute(f"""
            UPDATE Tasks SET status = '{task_status}', status_time = '{status_time}', exit_code = '{exit_code}', exit_reason = '{exit_reason}' WHERE userID= '{user}' AND taskID = '{task_id}'
        """)
        print('Updated table, waiting to commit...')
        connection.commit()
        print('committed')

        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(status)
        }
    except Exception as e:
        print('Error: ', e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f"failed to fetch status")
        }
    
    finally:
        cursor.close()
        connection.close()