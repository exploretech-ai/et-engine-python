import { confirmSignUp } from "@aws-amplify/auth";
import React, {useState, useEffect} from "react";

const BuildTab = ({idToken, activeTool}) => {

    const [buildStatus, setBuildStatus] = useState(null)

    useEffect(async () => {
        if(activeTool && idToken) {
            await fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools/" + activeTool.id + "/build", {
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
                setBuildStatus(status)
            })
            .catch(err => {
                console.log(err)
                setBuildStatus('Error Fetching Status')
            })
            
        }
    }, [activeTool, idToken])


    return (
        <div>{buildStatus}</div>
    )
}

export default BuildTab

