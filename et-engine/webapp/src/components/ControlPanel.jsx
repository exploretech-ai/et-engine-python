import React from "react";
import './ControlPanel.css'
import VFSPanel from "./Panels/VFSPanel";
import ToolsPanel from "./Panels/ToolsPanel";

const ControlPanel = ({style, activeTab, setActiveTab}) => {
    let Panel = null
    switch(activeTab) {
        case 'VFS':
            Panel = <VFSPanel/>
            break;
        case 'Tools':
            Panel = <ToolsPanel/>
            break;
    }
    return (
      <div className='main-content' style={style}>
        <h1>{activeTab}</h1>
        {Panel}
      </div>
    );
  }
  
export default ControlPanel