import json
import boto3
import db
import datetime

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

        status = task['lastStatus']
        print('Status: ', status)

        status_time = datetime.datetime.now()
        status_time = status_time.strftime('%Y-%m-%d %H:%M:%S')
        print('Status update time: ', status_time)

        cursor.execute(f"""
            UPDATE Tasks SET status = '{status}', status_time = '{status_time}' WHERE userID= '{user}' AND taskID = '{task_id}'
        """)
        print('Updated table...')
        connection.commit()

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