import json
from . import connect


def insert_graph(workflowID, graph):
    '''
    Creates a new algorithm ID and pushes to the database
    '''

    connection = connect()
    with connection.cursor() as cursor:
        sql_query = f"""
            UPDATE Workflows 
            SET graph = '{graph}'
            WHERE workflowID = '{workflowID}'
        """
        cursor.execute(sql_query)

    connection.commit()

    return sql_query

    
    

def handler(event, context):
    """
    This method does the following:

    1. reads the JSON submitted
    2. stores the JSON to a database (RDS Algo table)
    """

    try:
        workflowID = event['pathParameters']['workflowID']      
        graph_structure = json.loads(event['body'])

        #write JSON to database
        sql_query = insert_graph(workflowID, event['body'])

        return {
            'statusCode' : 200,
            'body' : json.dumps(graph_structure)
        }

        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error: {e} "}),
        }
    