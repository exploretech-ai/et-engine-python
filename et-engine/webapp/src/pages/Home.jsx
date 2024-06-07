import React, {useState} from "react"
import Page from "./Page"
import "./Home.css"

const Home = () => {

    
    return(
        <Page name={'Home'}>
            <div id="container">
                <div style={{flex:1}}>
                    <h2>Dashboard</h2> 
                    <ul>
                        <li>
                            X filesystems
                        </li>
                        <li>
                            Y tools
                        </li>
                        <li>
                            Z tasks running
                        </li>
                    </ul>
                </div>
                <div style={{flex:1}}>
                    <h2>Resources</h2>
                    <ul>
                        <li>
                            Viewer
                        </li>    
                        <li>
                            Python API
                        </li>
                        <li>
                            Documentation (link)
                        </li>
                        <li>
                            Support (link)
                        </li>
                    </ul> 
                </div>
            </div> 
        </Page>
    )
}

export default Home