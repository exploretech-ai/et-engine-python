import React, {useState, useEffect, act} from "react";
import { fetchAuthSession } from '@aws-amplify/auth';
import Navbar from "../components/Navbar";
import Directory from "../components/Directory";
import './Filesystems.css'
import Page from "./Page";
import FilesDragAndDrop from "../components/FilesDragAndDrop"

class VFS {
    constructor(name, id) {
        this.name = name
        this.id = id
        this.resource = "vfs"
    }
}

const NewVfsForm = ({idToken, setModalOpen, setLoading}) => {

    
    const [formData, setFormData] = useState({
        name: '',
        description: ''
    });

    const handleChange = (event) => {
        const { name, value } = event.target;
        setFormData({ ...formData, [name.slice(4)]: value });
    };

    const createNewVfs = async (event) => {
        event.preventDefault()
        setLoading(true)

        const response = await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs", {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + idToken
                },
                body: JSON.stringify({
                    name: formData.name,
                    description: formData.description
                })
            }
        ).then(response => {
            if (response.ok) {
                if (response.status == 200) {
                    throw Error('already exists')
                } else {
                    return response.json()
                }
            } else {
                throw Error(response.json())
            }
        }).then(newVfs => {

            console.log('new vfs', newVfs)

        }).catch(err => {
            
            console.log('could not create vfs', err)
        }).finally(() => {
            setModalOpen(false)
            setLoading(false)
        })
    }

    return (
        <>
            <h3>Create a new Filesystem</h3>
            <form onSubmit={async (e) => await createNewVfs(e)}>
                <label htmlFor="vfs-name">Name:</label><br/>
                <input type="text" id="vfs-name" name="vfs-name" value={formData.name} onChange={handleChange} required/><br/>
                
                <br/>
                
                <label htmlFor="vfs-description">Description (Optional):</label><br/>
                <textarea id="vfs-description" name="vfs-description" rows="4" value={formData.description} onChange={handleChange} /><br/>
                
                <input type="submit" value="Submit"/>
            </form>
        </> 
    )
}


const Modal = ({setModalOpen, idToken}) => {

    const [loading, setLoading] = useState(false)

    const closeModal = () => {
        setModalOpen(false);
    };

    return (
      <div className="modal">
        <div className="modal-content">
          <span className="close" onClick={closeModal}>&times;</span>
          {loading ? 
            <div>Creating new filesystem... </div>
            :
            <NewVfsForm idToken={idToken} setModalOpen={setModalOpen} setLoading={setLoading}/>
          }
        </div>
      </div>
    );
  }

const Filesystems = () => {
    const [idToken, setIdToken] = useState(null)
    const [activeVFS, setActiveVFS] = useState(new VFS(null, null))
    const [vfsData, setVfsData] = useState([])
    const [modalOpen, setModalOpen] = useState(false);
    const [loading, setLoading] = useState(true)
    const [filesLoading, setFilesLoading] = useState(true)
    const [path, setPath] = useState(['.'])

    const fetchToken = async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
            console.log(err);
        }
        setIdToken(session.tokens.idToken.toString())
    }


    const fetchFilesystems = () => {

        if (idToken) {
            console.log('Fetching available filesystems...')
            fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs", {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + idToken
                    }
                }
            ).then(response => {
                if (response.ok) {return response.json()}
                else {throw Error('error retrieving filesystems')}
            }).then(response => {
                const vfsIds = []
                const vfsNames = []
                const vfsMap = new Map()
                for (const [name, id] of response) {
                    vfsNames.push(name)
                    vfsMap.set(name, new VFS(name, id))
                }
                vfsNames.sort()
                for (const name of vfsNames) {
                    vfsIds.push(vfsMap.get(name))
                }
                setVfsData(vfsIds)
                setActiveVFS(vfsIds[0])
                setLoading(false)
                console.log('success')
            }).catch(error => {
                setLoading(false)
                console.error(error)
            })
        }
    };



    useEffect(() => {
        fetchToken()
        fetchFilesystems()
    }, [idToken])

    const openModal = () => {
        setModalOpen(true);
    };


    return (
        <Page name="Filesystems">
            <span id="vfs-header">
                <h2>Available Filesystems</h2> 
                <button onClick={openModal}>+ New</button>
            </span>
            {loading ?
                <div> Loading Filesystems... </div>
            :
                <div className="vfs-panel">
                    <Navbar 
                        resourceList={vfsData}
                        activeResource={activeVFS} 
                        setActiveResource={setActiveVFS} 
                        setFilesLoading={setFilesLoading} 
                        setPath={setPath} 
                        idToken={idToken}
                        style={{flex: 1, borderRight: '1px dashed gray'}}
                    />
                    <FilesDragAndDrop activeVFS={activeVFS} idToken={idToken}>
                        <Directory 
                            style={{flex: 5}} 
                            idToken={idToken} 
                            resource={activeVFS} 
                            loading={filesLoading} 
                            setLoading={setFilesLoading} 
                            command={"/list"}
                            path={path}
                            setPath={setPath}
                        />
                    </FilesDragAndDrop>
                </div>
            }
            {modalOpen && <Modal setModalOpen={setModalOpen} idToken={idToken}/>}
        </Page>
    )
}

export default Filesystems