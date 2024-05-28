import React from "react"
import './Navbar.css'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {faTrash} from '@fortawesome/free-solid-svg-icons'

const Tab = ({resource, activeResource, setActiveResource, setFilesLoading, setPath, idToken}) => {

    const handleTabClick = (resource) => {
        setActiveResource(resource); // Update active tab state when clicked
        if (setFilesLoading) {
            setFilesLoading(true)
        }
        if (setPath) {
            setPath(['.'])
        }
      };

    const deleteItem = async (e) => {
        e.stopPropagation()

        if (idToken) {
            console.log('Delete requested for ' + resource.resource, resource.name )
        

            const url = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/" + resource.resource + "?" + new URLSearchParams({
                name: resource.name
            })
            console.log(url)
            fetch(url, {
                method: "DELETE",
                headers: {
                    "Authorization": "Bearer " + idToken
                }
            })
            .then(response => {
                console.log('success: ', response)
            })
            .catch(error => {
                console.log('error', error)
            })
        } else {
            console.log('Delete requested, but ID token not found')
        }
    }

    return (
        <li key={resource.name}>
            <a className={activeResource.id === resource.id ? 'active' : ''} onClick={() => handleTabClick(resource)}>
                <p style={{flex:100}}>{resource.name}</p>
                <FontAwesomeIcon icon={faTrash} className="icon" style={{flex: 1}} onClick={deleteItem}/>
            </a>
        </li>
    )
}

const Navbar = ({resourceList, activeResource, setActiveResource, setFilesLoading, setPath, idToken, style}) => {

    const tabs = []
    const resourceNames = []
    const resourceMap = new Map()
    if (resourceList && activeResource) {
        for (const resource of resourceList) {
            resourceNames.push(resource.name)
            resourceMap.set(resource.name, resource)
            
        }
        resourceNames.sort()
        for (const resource of resourceNames) {
            tabs.push(
                <Tab 
                    resource={resourceMap.get(resource)}
                    activeResource={activeResource}
                    setActiveResource={setActiveResource}
                    setFilesLoading={setFilesLoading}
                    setPath={setPath}
                    idToken={idToken}
                    key={resource}
                />
            )
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