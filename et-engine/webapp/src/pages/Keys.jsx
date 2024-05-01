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

    delete() {
        console.log(this.name + " is being deleted")
    }
}

const KeyItem = ({apiKey, updateList}) =>{

    const handleRemoveItem = (e) => {
        apiKey.delete()
        updateList(l => l.filter(item => item.id !== apiKey.id));
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
        ).then(response => response.json());
        // If successful, it will return the key, the name, and a datestamp
        console.log(response)

        
        // Now update the API keys state, incrementing the next key id
        let nextKeyID = 0
        for (const key of APIKeys) { 
            if (key.id >= nextKeyID) {nextKeyID = key.id + 1}
        }

        setAPIKeys([
            ...APIKeys,
            new Key(response.name, response.dateCreated, nextKeyID)
        ])
        
        updateShowKey(response.key)
    }

    return (
        <>
        {showKey ? 
            <>
                <h3>Here's your new key</h3>
                <p>Make sure to copy and store this key in a secure location. You will not be able to see this again. If you lose it, you will have to create another key. Once you have the key, you can add it to your environment by opening a terminal and typing EXPORT ET_ENGINE_API_KEY="..."</p>
                <div className="key-container">
                    <span onClick={() => navigator.clipboard.writeText(showKey)}>
                        <i class="fa fa-copy"></i>
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