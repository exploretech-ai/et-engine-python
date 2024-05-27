import React, {useState, useEffect} from "react"
import Page from "./Page"
import { fetchAuthSession } from '@aws-amplify/auth';
import "./Jobs.css"

const TaskList = ({taskList}) => {

    const tasks = []
    for (const task of taskList) {
        tasks.push(
            <div key={task.taskID}>
                <p style={{flex:20}}>Tool: {task.toolName}</p>
                <p>Status: {task.status}</p>
            </div>
        )
    }
    return (
        <div className="task-list">
            {tasks}
        </div>
    )
}

const Jobs = () => {

    const [idToken, setIdToken] = useState(null)
    const [loading, setLoading] = useState(true)
    const [taskList, setTaskList] = useState([])

    const fetchData = async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
            console.log(err);
        }
        setIdToken(session.tokens.idToken.toString())
    }

    useEffect(() => {
        console.log('initializing')

        fetchData()
        
        if (idToken){
            fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tasks", {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + idToken
                    }
            })
            .then(response => {
                if (response.ok) {
                    return response.json()
                } else {
                    throw new Error('failed to list')
                }
            })
            .then(tasks => {
                
                console.log('success: ', tasks)
                setTaskList(tasks)
                setLoading(false)
            })
            .catch(error => {
                console.error(error)
            })
        }
        
    }, [idToken])


    return(
        <Page name="Tasks">
            {/* This is where you can see the past, present, and pending jobs. */}
            <span id="task-header">
                <h2>Browse</h2> 
            </span>
            {loading ? 
                <div>Loading...</div>
            :
                <TaskList taskList={taskList} />
            }
        </Page>
    )
}

export default Jobs