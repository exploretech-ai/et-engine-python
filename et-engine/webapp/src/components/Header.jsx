import React from 'react'
import './Header.css'


const Header = ({user}) => {
    return (
      <div className='header'>
        User: {user.username}
      </div>
    )
  }

export default Header