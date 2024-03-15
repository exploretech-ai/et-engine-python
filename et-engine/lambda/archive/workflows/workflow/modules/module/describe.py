import json
import db           # Lambda hooks onto "handler" as an import from the base directory "lambda", hence `db` being directly imported


def get_graph(workflowID):
    '''
    fetches the graph column for the workflow id
    '''

    connection = db.connect()
    with connection.cursor() as cursor:
        sql_query = f"""
            SELECT graph 
            FROM Workflows
            WHERE workflowID = '{workflowID}'
        """
        cursor.execute(sql_query)
        graph = cursor.fetchone()
    
    connection.close()

    return json.loads(graph[0])



def handler(event, context):

    try:

        workflowID = event['pathParameters']['workflowID']
        moduleName = event['pathParameters']['moduleName']
        graph = get_graph(workflowID)

        module_type = graph["nodes"][moduleName]["type"]
        module_props = graph["nodes"][moduleName]["properties"]

        out = f"Type: {module_type}, Properties: {module_props}"
        
        return {
                'statusCode': 200,
                'body': json.dumps(out)
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error: {e} "}),
        }
    
