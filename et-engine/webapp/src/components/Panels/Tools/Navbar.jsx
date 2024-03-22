import React, { useState, useEffect } from "react";
import './Navbar.css'



const Navbar = ({toolData, activeTool, setActiveTool}) => {

    const tabs = []
    if (activeTool) {
        for (const tool of toolData) {
            tabs.push(<li key={tool.id}><a className={activeTool.name === tool.name ? 'active' : ''} onClick={() => handleTabClick(tool)}>{tool.name}</a></li>)
        }
    }

    const handleTabClick = (tabName) => {
        setActiveTool(tabName); // Update active tab state when clicked
      }; 
    return (
        <nav>
            <ul className='navbar-tabs'>
                {tabs}
            </ul>
        </nav>
    )
}

const ToolNavbar = ({toolData, activeTool, setActiveTool, style}) => {



    return (
        <div style={style}>
            {toolData && <Navbar toolData={toolData} activeTool={activeTool} setActiveTool={setActiveTool}/>}
        </div>
    )
    
}

export default ToolNavbar