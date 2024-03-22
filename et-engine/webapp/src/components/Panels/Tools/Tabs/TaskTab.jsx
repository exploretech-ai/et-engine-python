import React, {useEffect, useState} from "react";

const TaskTab = ({idToken, activeTool}) => {

    const [imageStatus, setImageStatus] = useState(null)

    useEffect(async () => {
        if(activeTool && idToken) {
            await fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools/" + activeTool.id + "/tasks", {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + idToken
                    }
                }
            )
            .then(response => {
                if (response.ok) {
                    return response.json()
                }
                throw new Error('bad request')
            })
            .then(status => {
                if (status) {
                    setImageStatus('READY')
                } else {
                    setImageStatus('NO IMAGE: please run "push" to start a build')
                }
            })
            .catch(err => {
                console.log(err)
                setImageStatus('Error Fetching Status')
            })
            
        }
    }, [activeTool, idToken])



    return (
        <div>{imageStatus}</div>
    )
}

export default TaskTab