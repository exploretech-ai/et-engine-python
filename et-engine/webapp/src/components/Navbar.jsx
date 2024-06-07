import React, { useState } from "react"
import './Navbar.css'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {faTrash, faShare} from '@fortawesome/free-solid-svg-icons'


const ShareModal = ({resource, idToken, closeModal}) => {

    const [grantee, setGrantee] = useState("")
    const [sharing, setSharing] = useState(false)
    const [shareResponseMessage, setShareResponseMessage] = useState("")

    const shareItem = async (e) => {
        e.preventDefault()
        console.log('Requesting to share with', grantee)
        setSharing(true)

        const url = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/" + resource.resource + "/" + resource.id + "/share"
        fetch(url, {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + idToken
            },
            body: JSON.stringify({
                grantee: grantee
            })
        }).then(response => {
            if (response.ok) {
                return response.json()
            } else {
                res.text().then(text => {
                    throw new Error(text)
                })
            }
        }).then(response => {
            console.log(response)
            setShareResponseMessage("success")
        }).catch(error => {
            console.error(error)
            setShareResponseMessage("failed:" + error)
            // Parse error and display on a page
        }).finally(() => {
            // setSharing(false)
        })
    }

    return (
      <div>
        <h3>Share '{resource.name}` with another user</h3>
        {sharing ?
            <div>sharing with `{grantee}`...{shareResponseMessage}</div>
        : 
            <form onSubmit={async (e) => await shareItem(e)}>
                <label>User ID:</label><br/>
                <input type="text" value={grantee} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" onChange={(e) => setGrantee(e.target.value)} required/><br/>
                <input type="submit" value="Share"/>
            </form>
        }
      </div>
    );
  }

const DeleteModal = ({resource, idToken, closeModal}) => {

    const deleteItem = async (e) => {
        e.stopPropagation()

        if (idToken) {
            console.log('Delete requested for ' + resource.resource, resource.name )

            // const url = "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/" + resource.resource + "?" + new URLSearchParams({
            //     name: resource.name
            // })
            // console.log(url)
            // fetch(url, {
            //     method: "DELETE",
            //     headers: {
            //         "Authorization": "Bearer " + idToken
            //     }
            // }).then(response => {
            //     console.log('success: ', response)
            // }).catch(error => {
            //     console.log('error', error)
            // })
        } else {
            console.log('Delete requested, but ID token not found')
        }
    }

    return (
        <div>
            <p>Are you sure you want to delete `{resource.name}`? This action cannot be undone.</p>
            <button onClick={deleteItem}>Yes</button>
            <button onClick={closeModal}>No</button>
        </div>
    )
}

const Modal = ({resource, setModalOpen, modalType, setModalType, idToken}) => {

    const closeModal = () => {
        setModalOpen(false)
        setModalType(null)
    }

    let subModal
    if (modalType && modalType === 'share') {
        subModal =  <ShareModal resource={resource} closeModal={closeModal} idToken={idToken}/>
    } else if (modalType && modalType == 'delete') {
        subModal = <DeleteModal resource={resource} closeModal={closeModal} idToken={idToken}/>
    } else {
        subModal = <div>Error: Invalid type</div>
    }

    return (
        <div className="modal">
          <div className="modal-content">
            <span className="close" onClick={closeModal}>&times;</span>
              {subModal}
          </div>
        </div>
      ); 
}


const Tab = ({resource, activeResource, setActiveResource, setContentLoading, setPath, idToken}) => {

    const [modalOpen, setModalOpen] = useState(false)
    const [modalType, setModalType] = useState(null)

    const handleTabClick = (resource) => {
        setActiveResource(resource); // Update active tab state when clicked
        if (setContentLoading) {
            setContentLoading(true)
        }
        if (setPath) {
            setPath(['.'])
        }
      };

    

    const openModal = (e, targetModal) => {
        e.stopPropagation()
        setModalOpen(true)
        setModalType(targetModal)
    }

    

    return (
        <li key={resource.name}>
            <a className={activeResource.id === resource.id ? 'active' : ''} onClick={() => handleTabClick(resource)}>
                <p style={{flex:100}}>{resource.name}</p>
                <FontAwesomeIcon icon={faShare} className="icon" style={{flex: 1}} onClick={(e) => openModal(e, 'share')}/>
                <FontAwesomeIcon icon={faTrash} className="icon" style={{flex: 1}} onClick={(e) => openModal(e, 'delete')}/>
            </a>
            {modalOpen && 
                <Modal 
                    setModalOpen={setModalOpen}
                    modalType={modalType} 
                    setModalType={setModalType}
                    idToken={idToken}
                    resource={resource}
                />
            }
        </li>
    )
}

const Navbar = ({resourceList, activeResource, setActiveResource, setContentLoading, setPath, idToken, style}) => {

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
                    setContentLoading={setContentLoading}
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