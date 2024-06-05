import React, {useState, useEffect, act} from "react";
import { fetchAuthSession } from '@aws-amplify/auth';
import Navbar from "../components/Navbar";
import './Tools.css'
import Page from "./Page";

class Tool {
    constructor(name, id, description) {
        this.name = name
        this.id = id
        this.description = description
        this.resource = "tools"
    }
}
class VFS {
    constructor(name, id) {
        this.name = name
        this.id = id
        this.resource = "vfs"
    }
}

const NewTaskForm = ({idToken, setModalOpen, setLoading, activeTool}) => {

    const [availableFilesystems, setAvailableFilesystems] = useState([])
    const [filesystems, setFilesystems] = useState([])
    const [memory, setMemory] = useState("8GB")
    const [cpu, setCpu] = useState("4vCPU")

    const [args, setArgs] = useState([])
    // const [args, setArgs] = useState([
    //     {id: 0, name: 'command_line_args', value: '"map-005/geology.tif" "map-005/prob_porphyry.tif" "map-005/prob_volcanics.tif" "map-005/prob_breccia.tif" "map-005/prob_limestone.tif" --nodata -9999 --other'},
    //     {id: 1, name: 'prefix', value: '/mnt/a3927777-c26b-484d-a74a-89eb163f88cc/'}
    // ])

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
                const vfsList = []
                const vfsNames = []
                const vfsMap = new Map()
                for (const [name, id] of response) {
                    vfsNames.push(name)
                    vfsMap.set(name, new VFS(name, id))
                }
                vfsNames.sort()
                for (const name of vfsNames) {
                    vfsList.push(vfsMap.get(name))
                }
                setAvailableFilesystems(vfsList)
                console.log('success')
            }).catch(error => {
                console.error(error)
            })
        }
    };

    useEffect(() => {
        fetchFilesystems()
    }, [idToken])

    const addFilesystem = () => {
        setFilesystems([...filesystems, { id: filesystems.length, value: '' }]);
    }

    const removeFilesystem = (id) => {
        setFilesystems(filesystems.filter(fs => fs.id !== id));
    }

    const updateFilesystems = (id, event) => {
        const newFilesystems = filesystems.map(fs => {
          if (fs.id === id) {
            return { ...fs, value: event.target.value };
          }
          return fs;
        });
        setFilesystems(newFilesystems);
    }

    const addArg = () => {
        setArgs([...args, { id: args.length, name: '', value: '' }]);
    }

    const removeArg = (id) => {
        setArgs(args.filter(arg => arg.id !== id));
    }

    const updateArgs = (id, field, event) => {
        const newArgs = args.map(arg => {
            if (arg.id == id) {
                return {...arg, [field]: event.target.value}
            }
            return arg
        })
        setArgs(newArgs)
    }

    const launchTask = (event) => {
        
        event.preventDefault();
        const hardware = {
            'filesystems': filesystems.map(fs => fs.value),
            'memory': memory,
            'cpu': cpu,
            'gpu': false,
        }

        setLoading(true)
        console.log('Launching task...')
        console.log('Hardware:', hardware)
        console.log('Args:', args);

        fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools/" + activeTool.id, {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + idToken
                },
                body: JSON.stringify({
                    hardware: hardware,
                    ...args.reduce((obj, item) => ({
                        ...obj,
                        [item.name]: item.value
                    }), {})
                })
        }).then(response => {
            if (response.ok) {
                return response.json()
            } else {
                throw new Error(response.json())
            }
        }).then(message => {
            console.log('success:', message)
        }).catch(err => {
            console.error(err)
        }).finally(() => {
            setModalOpen(false)
            setLoading(false)
        })
    }

    return (
        <div id="new-task-form">
            <h3>Launch a new Task for Tool `{activeTool.name}`</h3>
            <form onSubmit={launchTask}>
                
                <label>Filesystems:</label><br/>
                <button type="button" onClick={addFilesystem}>Add Filesystem</button>
                {filesystems.map(fs => (
                    <div key={fs.id}>
                        <select
                            value={fs.value}
                            onChange={(e) => updateFilesystems(fs.id, e)}
                        >
                            <option key="-1" value="-1">
                                --
                            </option>
                            {availableFilesystems.map(available => (
                                <option key={available.id} value={available.name}>
                                    {available.name}
                                </option>
                            ))}
                        </select>
                        <button type="button" onClick={() => removeFilesystem(fs.id)}>Remove</button>
                    </div>
                ))}
                <br/>

                <label htmlFor="memory">Memory:</label>
                <input type="text" id="memory" name="memory" value={memory} onChange={(e) => setMemory(e.target.value)}/><br/>
                
                <label htmlFor="cpu">CPU:</label>
                <input type="text" id="cpu" name="cpu" value={cpu} onChange={(e) => setCpu(e.target.value)}/><br/>
                
                <label>Args:</label><br/>
                <button type="button" onClick={addArg}>Add Arg</button>
                {args.map(arg => (
                    <div key={arg.id}>
                        <input
                            type="text"
                            value={arg.name}
                            onChange={(e) => updateArgs(arg.id, "name", e)}
                        />
                        <input
                            type="text"
                            value={arg.value}
                            onChange={(e) => updateArgs(arg.id, "value", e)}
                        />
                        
                        <button type="button" onClick={() => removeArg(arg.id)}>Remove</button>
                    </div>
                ))}
                <br/>

                <input type="submit" value="Submit"/>
            </form>
        </div> 
    )
}

const Modal = ({setModalOpen, idToken, activeTool}) => {

    const [loading, setLoading] = useState(false)

    return (
      <div className="modal">
        <div className="modal-content">
          <span className="close" onClick={() => setModalOpen(false)}>&times;</span>
          {loading ? 
            <div>Launching task... </div>
            :
            <NewTaskForm idToken={idToken} setModalOpen={setModalOpen} setLoading={setLoading} activeTool={activeTool}/>
          }
        </div>
      </div>
    );
}

const ToolContent = ({idToken, activeTool, loading, setLoading, style}) => {

    const [toolInfo, setToolInfo] = useState({})
    const [modalOpen, setModalOpen] = useState(false);

    const describeTool = () => {
        if (activeTool && idToken) {
            console.log('Fetching details for tool', activeTool.name)
            fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools/" + activeTool.id, {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + idToken
                    }
            }).then(response => {
                if (response.ok) {return response.json()}
                else {throw Error('error describing tool', activeTool.name)}
            }).then(description => {
                setToolInfo(description)
                console.log('success:', description)
                setLoading(false)
            }).catch(error => {
                setLoading(false)
                console.error(error)
            })
        }
    }

    useEffect(() => {
        describeTool()
    }, [activeTool, idToken])

    return (
        <div style={style}>
            {loading ?
                <div>Loading tool contents...</div>
            :
            <div id="tool-content">
                <h3>Tool `{activeTool.name}`</h3>
                <p>Status: {toolInfo.ready ? "Ready" : "Not Ready"}</p>
                <p>Build: {toolInfo.buildStatus}</p>
                <button onClick={() => setModalOpen(true)}>Launch New Task</button>
            </div>
            }
            {modalOpen && <Modal setModalOpen={setModalOpen} idToken={idToken} activeTool={activeTool}/>}
        </div>
    )
}

const Tools = () => {
    
    const [idToken, setIdToken] = useState(null)
    const [activeTool, setActiveTool] = useState(null)
    const [toolData, setToolData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [toolLoading, setToolLoading] = useState(true)

    const fetchToken = async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
          console.error(err);
        }
        setIdToken(session.tokens.idToken.toString())
    }
    
    const fetchTools = () => {
        if (idToken) {
            console.log('Fetching available tools...')
            fetch(
                "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/tools", {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + idToken
                    }
            }).then(response => {
                if (response.ok) {return response.json()}
                else {throw Error('error retrieving tools')}
            }).then(response => {
                const tools = []
                const toolNames = []
                const toolMap = new Map()
                for (const [name, id] of response) {
                    toolNames.push(name)
                    toolMap.set(name, new Tool(name, id))
                }
                toolNames.sort()
                for (const name of toolNames) {
                    tools.push(toolMap.get(name))
                }
                setToolData(tools)
                setActiveTool(tools[0])
                setLoading(false)
                console.log('success')
            }).catch(error => {
                setLoading(false)
                console.error(error)
            })
        }
    }

    useEffect(() => {
        fetchToken()
        fetchTools()
    }, [idToken])

    return (
        <Page name="Tools">
            <h2>Available Tools</h2>
            {loading ?
                <div> Loading Tools... </div>
            :
                <div className="tool-panel">
                    <Navbar 
                        resourceList={toolData} 
                        activeResource={activeTool} 
                        setActiveResource={setActiveTool} 
                        idToken={idToken} 
                        setContentLoading={setToolLoading}
                        style={{flex: 1}}
                    />
                    <ToolContent 
                        idToken={idToken} 
                        activeTool={activeTool} 
                        loading={toolLoading}
                        setLoading={setToolLoading} 
                        style={{flex:3}}
                    />
                </div>
            }
        </Page>
    )
}

export default Tools