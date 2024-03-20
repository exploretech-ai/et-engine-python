import React, {useState} from "react";
import './Navbar.css'

const Navbar = ({style, activeTab, setActiveTab}) => {
    
    const handleTabClick = (tabName) => {
      setActiveTab(tabName); // Update active tab state when clicked
    }; 
    return (
      <nav style={style}>
        <ul className="navbar-tabs">
          <li><a href="#" className={activeTab === 'VFS' ? 'active' : ''} onClick={() => handleTabClick('VFS')}>Virtual File Systems</a></li>
          <li><a href="#" className={activeTab === 'Tools' ? 'active' : ''} onClick={() => handleTabClick('Tools')}>Tools</a></li>
        </ul>
      </nav>
    );
  
  }

export default Navbar