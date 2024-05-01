import React from "react";
import './Page.css'


const Page = ({name, children}) => {
    return (
        <div className="page">
            <div className="page-header">
                <h1>{name}</h1>
            </div>
            <div className="page-content">
                {children}
            </div>
        </div>
    )
}

export default Page