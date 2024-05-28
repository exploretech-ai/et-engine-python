import React, {useState, useEffect} from "react"
import Page from "./Page"
import { fetchAuthSession } from '@aws-amplify/auth';
import "./Jobs.css"

const TaskArgs = ({task}) => {

    const taskArgs = []
    for (const arg of task.args) {
        taskArgs.push(
            <p key={arg.name}>{arg.name}: {arg.value}</p>
        )
    }
    return(
        <div>
            Arguments:
            {taskArgs}
        </div>
    )
}

const TaskHardware = ({task}) => {

    const filesystems = []
    for (const fs of task.hardware.filesystems) {
        filesystems.push(
            <p key={fs}>{fs}</p>
        )
    }
    return(
        <div>
            <p>CPU: {task.hardware.cpu}</p>
            <p>GPU: {task.hardware.gpu}</p>
            <p>Memory: {task.hardware.memory}</p>
            <span>
                Filesystems: {filesystems}
            </span>
        </div>
    )
}


const TaskDropdown = ({task}) => {
    return(
        <div className="task-dropdown">
            <TaskArgs task={task}/>
            <TaskHardware task={task}/>
            <p>Exit Code: {task.exitCode}</p>
            <p>Exit Reason: {task.exitReason}</p>
        </div>
    )
}

const Task = ({task}) => {

    const [showDropdown, setDropdown] = useState(false)

    return(
        <div>
            <div className="task" onClick={() => setDropdown(!showDropdown)}>
                <p style={{flex:2}}>Tool: {task.toolName}</p>
                <p style={{flex:2}}>{task.startTime}</p>
                <p style={{flex:2}}>Status: {task.status}</p>
            </div>
            {showDropdown && 
                <TaskDropdown task={task} />
            }
        </div>
    )
}

const TaskList = ({taskList}) => {

    const tasks = []
    for (const task of taskList) {
        tasks.push(
            <Task task={task} key={task.taskID}/>
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

    const fetchToken = async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
            console.log(err);
        }
        setIdToken(session.tokens.idToken.toString())
    }

    const fetchTasks = () => {
        
        if (idToken){
            console.log('Fetching available tasks...')
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

                const orderedTasks = []
                const taskList = []
                const taskMap = new Map()
                let i = 0
                for (const task of tasks) {
                    taskList.push([task.startTime, i])
                    taskMap.set(i, task)
                    i ++
                }
                taskList.sort().reverse()
                for (const [time, index] of taskList) {
                    orderedTasks.push(taskMap.get(index))
                }
                setTaskList(orderedTasks)
                setLoading(false)
            })
            .catch(error => {
                console.error(error)
            })
        }
    }

    useEffect(() => {
        
        fetchToken()
        fetchTasks()
        
    }, [idToken])

    const clearTasks = () => {

        setLoading(true)
        console.log('Task clearing requested')
        const url = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tasks"
        fetch(url, {
            method: "DELETE",
            headers: {
                "Authorization": "Bearer " + idToken
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json()
            } else {
                throw new Error('error clearing tasks')
            }
        })
        .then(message => {
            console.log("success, returned message ", message)
            fetchTasks()
        })
        .catch(error => {
            console.error(error)
            setLoading(false)
        })
    }


    return(
        <Page name="Tasks">
            <span id="task-header">
                <h2>Browse</h2> 
                <button onClick={clearTasks}>Clear</button>
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