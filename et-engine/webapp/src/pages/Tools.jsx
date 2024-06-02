import React, {useState, useEffect, act} from "react";
import { fetchAuthSession } from '@aws-amplify/auth';
import Navbar from "../components/Navbar";
import './Tools.css'
import Page from "./Page";

class Tool {
    
    constructor(name, id, description) {
        this.name = name
        this.id = id
        this.description = description
        this.resource = "tools"
    }
}

const ToolContent = ({idToken, activeTool, loading, setLoading, style}) => {

    const [toolInfo, setToolInfo] = useState({})

    const describeTool = () => {
        if (activeTool && idToken) {
            console.log('Fetching details for tool', activeTool.name)
            fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools/" + activeTool.id, {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + idToken
                    }
            }).then(response => {
                if (response.ok) {return response.json()}
                else {throw Error('error describing tool', activeTool.name)}
            }).then(description => {
                setToolInfo(description)
                console.log('success:', description)
                setLoading(false)
            }).catch(error => {
                setLoading(false)
                console.error(error)
            })
        }
    }

    useEffect(() => {
        describeTool()
    }, [activeTool, idToken])

    return (
        <div style={style}>
            {loading ?
                <div>Loading tool contents...</div>
            :
            <div>
                <p>Status: {toolInfo.ready ? "Ready" : "Not Ready"}</p>
                <p>Build Info: {toolInfo.buildStatus}</p>
                <button>New Task</button>
            </div>
            }
        </div>
        
    )
}

const Tools = () => {
    
    const [idToken, setIdToken] = useState(null)
    const [activeTool, setActiveTool] = useState(null)
    const [toolData, setToolData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [toolLoading, setToolLoading] = useState(true)

    const fetchToken = async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
          console.error(err);
        }
        setIdToken(session.tokens.idToken.toString())
    }
    
    const fetchTools = () => {
        if (idToken) {
            console.log('Fetching available tools...')
            fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools", {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + idToken
                    }
            }).then(response => {
                if (response.ok) {return response.json()}
                else {throw Error('error retrieving tools')}
            }).then(response => {
                const tools = []
                const toolNames = []
                const toolMap = new Map()
                for (const [name, id] of response) {
                    toolNames.push(name)
                    toolMap.set(name, new Tool(name, id))
                }
                toolNames.sort()
                for (const name of toolNames) {
                    tools.push(toolMap.get(name))
                }
                setToolData(tools)
                setActiveTool(tools[0])
                setLoading(false)
                console.log('success')
            }).catch(error => {
                setLoading(false)
                console.error(error)
            })
        }
    }

    useEffect(() => {
        fetchToken()
        fetchTools()
    }, [idToken])

    return (
        <Page name="Tools">
            <h2>Available Tools</h2>
            {loading ?
                <div> Loading Tools... </div>
            :
                <div className="tool-panel">
                    <Navbar 
                        resourceList={toolData} 
                        activeResource={activeTool} 
                        setActiveResource={setActiveTool} 
                        idToken={idToken} 
                        setContentLoading={setToolLoading}
                        style={{flex: 1}}
                    />
                    <ToolContent 
                        idToken={idToken} 
                        activeTool={activeTool} 
                        loading={toolLoading}
                        setLoading={setToolLoading} 
                        style={{flex:3}}
                    />
                </div>
            }
        </Page>
    )
}

export default Tools