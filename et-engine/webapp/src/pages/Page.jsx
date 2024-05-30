import React from "react";
import './Page.css'


const Page = ({name, children, style}) => {
    return (
        <div className="page">
            <div className="page-header">
                <h1>{name}</h1>
            </div>
            <div className="page-content" style={style}>
                {children}
            </div>
        </div>
    )
}

export default Page