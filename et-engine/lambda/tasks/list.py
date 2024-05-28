import json
import db

def handler(event, context):

    connection = db.connect()
    cursor = connection.cursor()
    try:
        user = event['requestContext']['authorizer']['userID']
        print('User requested task list: ', user)

        query = f"""
            SELECT taskID, toolID, logID, start_time, hardware, args, status, status_time, exit_code, exit_reason FROM Tasks WHERE userID = '{user}'
        """
        print(query)

        cursor.execute(query)
        print('fetched tasks')

        task_list = cursor.fetchall()
        print('task list data: ', task_list)

        tasks = []
        for row in task_list:

            tool_id = row[1]
            cursor.execute(f"""
                SELECT name FROM Tools WHERE toolID = '{tool_id}'
            """)
            tool_name = cursor.fetchone()[0]
            tasks.append({
                'taskID':       row[0],
                'toolName':     tool_name,
                'logID':        row[2],
                'startTime':   row[3].strftime('%Y-%m-%d %H:%M:%S'),
                'hardware':     row[4],
                'args':         row[5],
                'status':       row[6],
                'statusTime':  row[7].strftime('%Y-%m-%d %H:%M:%S'),
                'exitCode':     row[8],
                'exitReason':   row[9]
            })
        print('task list JSON: ', tasks)

        return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(tasks)
            }
        
    except Exception as e:
        print('error: ', e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'error fetching list')
        }
    finally:
        cursor.close()
        connection.close()
    
