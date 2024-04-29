import React, {useState, useEffect} from 'react'
import './App.css'


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





function App() {
  const [activeTab, setActiveTab] = useState('VFS')



  return (
    <Authenticator loginMechanisms={['email']} hideSignUp={true}>
    {({signOut, user}) => (
      <div className="App">
        <Header user={user} />
        <div className='main-container'>
          <Navbar activeTab={activeTab} setActiveTab={setActiveTab} style={{flex: 1}}/>
          <ControlPanel activeTab={activeTab} setActiveTab={setActiveTab} style={{flex: 3}}/>
        </div>
        
    </div>
    )}
    </Authenticator>
  );
}

export default App

