import React, {useState, useEffect} from 'react'
import './App.css'
import { Outlet, Link } from "react-router-dom";


import {Amplify} from 'aws-amplify'
import { Authenticator } from '@aws-amplify/ui-react'
import '@aws-amplify/ui-react/dist/styles.css';


Amplify.configure({
  Auth: {
    Cognito: {
      userPoolClientId: '7veifuegtpskqerl7b2lakdfdn',
      userPoolId: 'us-east-2_c3KpcMfzh'
    }
    
  }
})


const Header = ({user}) => {
  return (
    <div id="header">
      <div>User ID: </div>
      <div>{user.username}</div>
    </div>
  )
}



const Sidebar = ({user}) => {
  return(
  <div id="sidebar">
    
      <h1>The Engine</h1>
      <Header user={user} />
      <nav>
        <ul>
          <li>
            <Link to={`home`}>Home</Link>
          </li>
          <li>
            <Link to={`filesystems`}>Filesystems</Link>
          </li>
          <li>
            <Link to={`tools`}>Tools</Link>
          </li>
          <li>
            <Link to={`jobs`}>Compute Jobs</Link>
          </li>
          <li>
            <Link to={`share`}>Share</Link>
          </li>
          <li>
            <Link to={`keys`}>API Keys</Link>
          </li>
        </ul>
      </nav>
    </div>
  )
}


function App() {
  return (
    <Authenticator loginMechanisms={['email']} hideSignUp={true}>
    {({signOut, user}) => (
      <>
        <Sidebar user={user}/>
        <div id="detail">
          <Outlet/>
        </div>
    </>
    )}
    </Authenticator>
  );
}

export default App

