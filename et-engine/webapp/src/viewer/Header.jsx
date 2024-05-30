import React, { useEffect } from "react";
import { useAuthenticator } from "@aws-amplify/ui-react";

function Header({ setAuthVisible }) {
    const { user, signOut } = useAuthenticator((context) => [context.user])

    return (
        <div id="header">
            {user ?  <LogOutButton signOut={signOut} setAuthVisible={setAuthVisible}/>: <LogInButton setAuthVisible={setAuthVisible}/> }
            email: {user ? (user.attributes ? user.attributes.email : 'None') : 'None'}
        </div>
    )
}

function LogInButton({setAuthVisible}) {
    return (
        <button onClick={() => setAuthVisible(true)}> 
            Log In/Sign Up 
        </button>
    )
}

function LogOutButton({signOut, setAuthVisible}) {
    return(
        <button onClick={() => {signOut(); setAuthVisible(false)}}>
            Sign Out
        </button>
    )
}

export default Header