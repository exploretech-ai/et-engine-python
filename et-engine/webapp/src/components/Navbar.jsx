import React from "react"
import './Navbar.css'


const Navbar = ({resourceList, activeResource, setActiveResource, setFilesLoading, setPath, style}) => {

    // Navbar states
    // Default state
    // 

    const handleTabClick = (resource) => {
        setActiveResource(resource); // Update active tab state when clicked
        if (setFilesLoading) {
            setFilesLoading(true)
        }
        if (setPath) {
            setPath(['.'])
        }
      };

    const tabs = []
    if (resourceList && activeResource) {
        for (const resource of resourceList) {
            tabs.push(<li key={resource.name}><a className={activeResource.id === resource.id ? 'active' : ''} onClick={() => handleTabClick(resource)}>{resource.name}</a></li>)
        }
    }

    

    return (
        <div style={style}>
            {resourceList && 
            <nav>
                <ul className='navbar-tabs'>
                    {tabs}
                </ul>
            </nav>
            }
        </div>
    )
    
}

export default Navbar