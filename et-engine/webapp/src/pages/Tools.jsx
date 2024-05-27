import React, {useState, useEffect} from "react";
import { fetchAuthSession } from '@aws-amplify/auth';
import Navbar from "../components/Navbar";
import './Tools.css'
import Page from "./Page";

import CodeTab from "../components/CodeTab"; 
import BuildTab from "../components/BuildTab"
import TaskTab from "../components/TaskTab";
// import ToolTabs from "../components/ToolTabs"

class Tool {
    constructor(name, id, description) {
        this.name = name
        this.id = id
        this.description = description
        this.resource = "tools"
    }
}

class Tab {
    constructor(name, resource) {
        this.name = name
        this.resource = resource
    }
}


const ToolContent = ({idToken, activeTool, style}) => {
    
    const [activeTab, setActiveTab] = useState(new Tab('Build', {...activeTool}))

    useEffect(() => {
        setActiveTab(new Tab(activeTab.name, {...activeTool}))
    }, [activeTool])

    return (
            <div style={style}>
                <div className="tool-tab" style={style}>
                    {/* <div onClick={() => setActiveTab(new Tab('Code', {...activeTool}))} className={activeTab.name === 'Code' ? 'active' : ''}>
                        Code
                    </div> */}
                    <div onClick={() => setActiveTab(new Tab('Build', {...activeTool}))} className={activeTab.name === 'Build' ? 'active' : ''}>
                        Build
                    </div>
                    <div onClick={() => setActiveTab(new Tab('Tasks', {...activeTool}))} className={activeTab.name === 'Tasks' ? 'active' : ''}>
                        Tasks
                    </div>
                </div>
                {/* {activeTab.name === 'Code' && <CodeTab idToken={idToken} activeTool={activeTool}/>} */}
                {activeTab.name === 'Build' && <BuildTab idToken={idToken} activeTool={activeTool}/>}
                {activeTab.name === 'Tasks' && <TaskTab idToken={idToken} activeTool={activeTool}/>}
            </div>
    )
}

const Tools = () => {
    const [idToken, setIdToken] = useState(null)
    const [activeTool, setActiveTool] = useState(null)
    const [toolData, setToolData] = useState(null)
    const [loading, setLoading] = useState(true)


    const fetchData = async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
          console.log(err);
        }

        await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools", {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + session.tokens.idToken.toString()
                }
            }
        ).then(response => {
            if (response.ok) {return response.json()}
            else {throw Error('error retrieving key IDs')}
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
            setIdToken(session.tokens.idToken.toString())
            setLoading(false)
        }).catch(error => {
            setLoading(false)
            console.log(error)
        })
        
    };



    useEffect(async () => {
        await fetchData()
    }, [idToken])

    return (
        <Page name="Tools">
            <h2>Available Tools</h2>
            {loading ?
                <div> Loading Tools... </div>
            :
                <div className="tool-panel">
                    <Navbar resourceList={toolData} activeResource={activeTool} setActiveResource={setActiveTool} idToken={idToken} style={{flex: 1}}/>
                    <ToolContent idToken={idToken} activeTool={activeTool} style={{flex:3}}/>
                </div>
            }
        </Page>
    )


}

export default Tools