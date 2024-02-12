import React, { useState } from 'react'
import logo from './logo.svg'
import './App.css'
import UserID from './components/UserID'
import AlgorithmsList from './components/Algorithm'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <header className="App-header">
        <UserID/>
        <AlgorithmsList/>
      </header>
    </div>
  )
}

export default App
