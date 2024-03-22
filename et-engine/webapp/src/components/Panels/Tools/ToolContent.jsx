import React, {useState, useEffect} from "react";
import ToolTabs from "./ToolTabs";

import CodeTab from "./Tabs/CodeTab";
import BuildTab from "./Tabs/BuildTab";
import TaskTab from "./Tabs/TaskTab";

const ToolContent = ({idToken, activeTool, style}) => {
    const [activeTab, setActiveTab] = useState('Code')

    let tab = null
    switch(activeTab){
        case 'Code':
            tab = <CodeTab idToken={idToken} activeTool={activeTool}/>
            break;
        case 'Build':
            tab = <BuildTab idToken={idToken} activeTool={activeTool}/>
            break;
        case 'Tasks':
            tab = <TaskTab idToken={idToken} activeTool={activeTool}/>
            break;
    }


    return (
        <div style={style}>
            <ToolTabs activeTab={activeTab} setActiveTab={setActiveTab}/>
            {tab && tab}
        </div>
    )
}

export default ToolContent