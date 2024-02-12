import React, { useState } from 'react'
import logo from './logo.svg'
import './App.css'
import UserID from './components/UserID'
import AlgorithmsList from './components/Algorithm'

function App() {
  const [userID, setUserID] = useState('');

  return (
    <div className="App">
      <header className="App-header">
        <UserID userID={userID} setUserID={setUserID}/>
      </header>
    </div>
  )
}

export default App
