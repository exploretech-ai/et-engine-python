import React, {useState, useEffect} from "react";
import { fetchAuthSession } from '@aws-amplify/auth';
import VFSNavbar from "./Filesystems/Navbar";
import Directory from "./Filesystems/Directory";
import './Filesystems.css'
import Page from "./Page";

class VFS {
    constructor(name, id) {
        this.name = name
        this.id = id
    }
}



const Filesystems = () => {
    const [idToken, setIdToken] = useState(null)
    const [activeVFS, setActiveVFS] = useState(null)
    const [vfsData, setVfsData] = useState(null)


    const fetchData = async () => {

        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
            console.log(err);
        }
        setIdToken(session.tokens.idToken.toString())


        const result = await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs", {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + session.tokens.idToken.toString()
                }
            }
        ).then(response => {
            if (response.ok) {
                return response.json()
            } else {
                throw Error('could not fetch VFS list')
                // return response.json()
            }
        }).catch(error => {
            console.log(error)
            return false
        })

        if (result) {
            const vfsIds = []
            for (const name of result) {
                // Get the VFS ID's for each VFS
                const id = await fetch(
                    "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs?" + new URLSearchParams({name: name}), {
                        method: "GET",
                        headers: {
                            "Authorization": "Bearer " + session.tokens.idToken.toString()
                        }
                    }
                )
                .then(response => {
                    if (response.ok) {return response.json()}
                    else {throw Error('could not fetch vfs')}
                }).catch(error => {
                    console.log(error)
                })

                vfsIds.push(new VFS(name, id))
            }
            setVfsData(vfsIds)
            setActiveVFS(vfsIds[0])
        }
        
        
    };



    useEffect(async () => {
        await fetchData()
    }, [])



    return (
        <Page name="Filesystems">
            <div className="vfs-panel">
                <VFSNavbar vfsData={vfsData} activeVFS={activeVFS} setActiveVFS={setActiveVFS} style={{flex: 1}}/>
                <Directory style={{flex: 5}} idToken={idToken} activeVFS={activeVFS}/>
            </div>
        </Page>
    )
}

export default Filesystems