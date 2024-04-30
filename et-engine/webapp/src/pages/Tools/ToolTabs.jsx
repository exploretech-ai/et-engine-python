import React from "react";
import './ToolTabs.css'

const Tab = ({name, activeTab, setActiveTab}) => {



    return (
        <div onClick={() => setActiveTab(name)} className={activeTab === name ? 'active' : ''}>
            {name}
        </div>
    )
}

const ToolTabs = ({activeTab, setActiveTab, style}) => {

    return (
        <div className="tool-tab" style={style}>
            <Tab name={'Code'} activeTab={activeTab} setActiveTab={setActiveTab}/>
            <Tab name={'Build'} activeTab={activeTab} setActiveTab={setActiveTab}/>
            <Tab name={'Tasks'} activeTab={activeTab} setActiveTab={setActiveTab}/>
        </div>
    )
}

export default ToolTabs