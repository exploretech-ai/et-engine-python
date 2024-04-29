import React, {useState, useEffect} from 'react'
// import './App.css'


import {Amplify} from 'aws-amplify'
import { Authenticator } from '@aws-amplify/ui-react'
import '@aws-amplify/ui-react/dist/styles.css';

import Header from './components/Header';
import Navbar from './components/Navbar';
import ControlPanel from './components/ControlPanel';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolClientId: '7veifuegtpskqerl7b2lakdfdn',
      userPoolId: 'us-east-2_c3KpcMfzh'
    }
    
  }
})


const Sidebar = ({user}) => {
  return(
  <div id="sidebar">
    
      <h1>The Engine</h1>
      <Header user={user} />
      <nav>
        <ul>
          <li>
            <a href={`/filesystems`}>Filesystems</a>
          </li>
          <li>
            <a href={`/tools`}>Tools</a>
          </li>
          <li>
            <a href={`/tools`}>Keys</a>
          </li>
        </ul>
      </nav>
    </div>
  )
}


function App() {
  const [activeTab, setActiveTab] = useState('VFS')



  return (
    <Authenticator loginMechanisms={['email']} hideSignUp={true}>
    {({signOut, user}) => (
      <>
        <Sidebar user={user}/>
        <div id="detail">
          
          <div className='main-container'>
            <Navbar activeTab={activeTab} setActiveTab={setActiveTab} style={{flex: 1}}/>
            <ControlPanel activeTab={activeTab} setActiveTab={setActiveTab} style={{flex: 3}}/>
          </div>
        </div>
    </>
    )}
    </Authenticator>
  );
}

export default App

