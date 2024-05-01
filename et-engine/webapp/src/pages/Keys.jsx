import React from "react"
import { useState, useEffect } from "react"
import Page from "./Page"
import "./Keys.css"
import { fetchAuthSession } from '@aws-amplify/auth';

class Key {
    constructor(name, date, id) {
        this.name = name
        this.date = date
        this.id = id // NOTE: this is not the key, this is only for the purposes 
    }

    async delete(idToken) {
        const response = await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/keys?" + new URLSearchParams({
                name: this.name
            }), {
                method: "DELETE",
                headers: {
                    "Authorization": "Bearer " + idToken
                }
            }
        ).then(response => {
            if (response.ok) {
                return true
            } else {
                console.log('NOT OK')
                throw Error
            }
        }).catch(err => {
            console.log('ERROR')
            return false
        })
        return response
        // console.log(this.name + " is being deleted client-side only. Server-side deletion not yet supported.")
    }
}


const KeyItem = ({apiKey, updateList, idToken}) =>{

    const handleRemoveItem = async (e) => {
        const success = await apiKey.delete(idToken)
        if (success) {
            updateList(l => l.filter(item => item.id !== apiKey.id));
        }
        
    };
    
    return(
        <div>
            <p style={{flex: 2}}>{apiKey.name}</p>
            <p style={{flex: 2}}>Date Created: {apiKey.date}</p>
            <span className="delete-icon" onClick={handleRemoveItem}>
                <i className="fa fa-trash fa-lg"></i>
            </span>
        </div>
    )
}


const NewKeyForm = ({idToken, APIKeys, setAPIKeys, showKey, updateShowKey}) => {

    
    const [formData, setFormData] = useState({
        name: '',
        description: ''
    });

    const handleChange = (event) => {
        const { name, value } = event.target;
        setFormData({ ...formData, [name.slice(4)]: value });
    };

    const createNewKey = async (event) => {
        event.preventDefault()

        const response = await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/keys", {
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
        }).then(newKey => {

            // Now update the API keys state, incrementing the next key id
            let nextKeyID = 0
            for (const key of APIKeys) { 
                if (key.id >= nextKeyID) {nextKeyID = key.id + 1}
            }

            setAPIKeys([
                ...APIKeys,
                new Key(newKey.name, newKey.dateCreated, nextKeyID)
            ])
            
            updateShowKey(newKey.key)

        }).catch(err => {
            
            if (err.message.includes('already exists')) {
                updateShowKey('Error: key "' + formData.name + '" already exists. Please try again with a different name.')
            } else {
                updateShowKey('An unknown error occurred. Please try again.')
            }
            // console.log('could not create key')
        })

        
        
    }

    return (
        <>
        {showKey ? 
            <>
                <h3>Here's your new key</h3>
                <p>Make sure to copy and store this key in a secure location. You will not be able to see this again. If you lose it, you will have to create another key.</p>
                <div className="key-container">
                    <span onClick={() => navigator.clipboard.writeText(showKey)}>
                        <i className="fa fa-copy"></i>
                    </span>
                    <p>{showKey}</p>
                </div>
                
            </> :
            <>
                <h3>Create a new API key</h3>
                <form onSubmit={async (e) => await createNewKey(e)}>
                    <label htmlFor="key-name">Key Name:</label><br/>
                    <input type="text" id="key-name" name="key-name" value={formData.name} onChange={handleChange} required/><br/>
                    
                    <br/>
                    
                    <label htmlFor="key-description">Description (Optional):</label><br/>
                    <textarea id="key-description" name="key-description" rows="4" value={formData.description} onChange={handleChange} /><br/>
                    
                    <input type="submit" value="Submit"/>
                </form>
            </> 
        }
        </>
    )
}


const Modal = ({setModalOpen, idToken, APIKeys, setAPIKeys}) => {

    const [showKey, updateShowKey] = useState(false)

    const closeModal = () => {
        updateShowKey(false)
        setModalOpen(false);
    };

    return (
      <div className="modal">
        <div className="modal-content">
          <span className="close" onClick={closeModal}>&times;</span>
          <NewKeyForm idToken={idToken} APIKeys={APIKeys} setAPIKeys={setAPIKeys} showKey={showKey} updateShowKey={updateShowKey}/>
        </div>
      </div>
    );
  }
  

const Keys = () => {

    const [APIKeys, setAPIKeys] = useState([])
    const [modalOpen, setModalOpen] = useState(false);
    const [idToken, setIdToken] = useState(null)

    useEffect(async () => {
        let session = null
        try {
            session = await fetchAuthSession();   // Fetch the authentication session
        } catch (err) {
            console.log(err);
        }
        setIdToken(session.tokens.idToken.toString())

        const response = await fetch(
            "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/keys", {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + session.tokens.idToken.toString()
                }
            }
        ).then(
            response => response.json()
        ).then(response => {
            const newAPIKeys = []
            let nextKeyID = 0
            for (const item of response){
                newAPIKeys.push(new Key(item.name, item.dateCreated, nextKeyID))
                nextKeyID += 1
            }
            setAPIKeys(newAPIKeys)
        })
                
        
        

    }, [])

    const openModal = () => {
        setModalOpen(true);
    };

    

    return(
        <Page name={'API Keys'}>
            <span id="api-key-header">
                <h2>My Keys</h2> 
                <button onClick={openModal}>+ New</button>
            </span>
            <div className="list-container">
                {APIKeys.map((item, index) => <KeyItem key={index} apiKey={item} updateList={setAPIKeys} idToken={idToken}/>)}
            </div>
            {modalOpen && <Modal setModalOpen={setModalOpen} idToken={idToken} APIKeys={APIKeys} setAPIKeys={setAPIKeys}/>}
        </Page>
    )
}

export default Keys