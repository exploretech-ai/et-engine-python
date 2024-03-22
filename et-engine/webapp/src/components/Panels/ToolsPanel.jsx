import React, {useState, useEffect} from "react";
import { fetchAuthSession } from '@aws-amplify/auth';
import ToolNavbar from "./Tools/Navbar";
import ToolContent from "./Tools/ToolContent";
import './ToolsPanel.css'


class Tool {
    constructor(name, id, description) {
        this.name = name
        this.id = id
        this.description = description
    }
}

const ToolsPanel = () => {
    const [idToken, setIdToken] = useState(null)
    const [activeTool, setActiveTool] = useState(null)
    const [toolData, setToolData] = useState(null)


    const fetchData = async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
          console.log(err);
        }

        const response = await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools", {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + session.tokens.idToken.toString()
                }
            }
        );
        const result = await response.json();

        if (result) {
            const tools = []
            for (const name of result) {
                // Get the VFS ID's for each VFS
                const id = await fetch(
                    "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools?" + new URLSearchParams({name: name}), {
                        method: "GET",
                        headers: {
                            "Authorization": "Bearer " + session.tokens.idToken.toString()
                        }
                    }
                )
                .then(response => response.json())

                tools.push(new Tool(name, id))
            }
            setToolData(tools)
            setActiveTool(tools[0])
            setIdToken(session.tokens.idToken.toString())
        }
    };



    useEffect(async () => {
        await fetchData()
    }, [])

    return (
        <div className="tool-panel">
            <ToolNavbar toolData={toolData} activeTool={activeTool} setActiveTool={setActiveTool} style={{flex: 1}}/>
            <ToolContent idToken={idToken} activeTool={activeTool} style={{flex:3}}/>
        </div>
    )


}

export default ToolsPanel