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



const Filesystems = () => {
    const [idToken, setIdToken] = useState(null)
    const [activeVFS, setActiveVFS] = useState(new VFS(null, null))
    const [vfsData, setVfsData] = useState([])


    const fetchData = async () => {

        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
            console.log(err);
        }
        setIdToken(session.tokens.idToken.toString())

        await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs", {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + session.tokens.idToken.toString()
                }
            }
        ).then(response => {
            if (response.ok) {return response.json()}
            else {throw Error('error retrieving key IDs')}
        }).then(response => {
            const vfsIds = []
            for (const [name, id] of response) {
                vfsIds.push(new VFS(name, id))
            }
            setVfsData(vfsIds)
            setActiveVFS(vfsIds[0])
        }).catch(error => {
            console.log(error)
            return false
        })
        
    };



    useEffect(async () => {
        await fetchData()
    }, [])



    // const map1 = 
    // console.log(vfsData.map(element => element.name))
    return (
        <Page name="Filesystems">
            <h2>Available Filesystems</h2>
            <div className="vfs-panel">
                <Navbar resourceList={vfsData} activeResource={activeVFS} setActiveResource={setActiveVFS} style={{flex: 1, 'border-right': '1px dashed gray'}}/>
                <FilesDragAndDrop activeVFS={activeVFS} idToken={idToken}>
                    <Directory style={{flex: 5}} idToken={idToken} resource={activeVFS} command={"/list"}/>
                </FilesDragAndDrop>
            </div>
        </Page>
    )
}

export default Filesystems