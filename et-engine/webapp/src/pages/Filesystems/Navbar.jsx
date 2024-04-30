import React, { useState, useEffect } from "react";
import './Navbar.css'



const Navbar = ({vfsData, activeVFS, setActiveVFS}) => {

    const tabs = []
    if (activeVFS) {
        for (const vfs of vfsData) {
            tabs.push(<li key={vfs.id}><a className={activeVFS.name === vfs.name ? 'active' : ''} onClick={() => handleTabClick(vfs)}>{vfs.name}</a></li>)
        }
    }

    const handleTabClick = (tabName) => {
        setActiveVFS(tabName); // Update active tab state when clicked
      }; 
    return (
        <nav>
            <ul className='navbar-tabs'>
                {tabs}
            </ul>
        </nav>
    )
}

const VFSNavbar = ({vfsData, activeVFS, setActiveVFS, style}) => {



    return (
        <div style={style}>
            {vfsData && <Navbar vfsData={vfsData} activeVFS={activeVFS} setActiveVFS={setActiveVFS}/>}
        </div>
    )
    
}

export default VFSNavbar