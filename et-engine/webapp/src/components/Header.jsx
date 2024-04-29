import React from 'react'
import './Header.css'


const Header = ({user}) => {
    return (
      <div id="header">
        <div>User ID: </div>
        <div>{user.username}</div>
      </div>
    )
  }

export default Header