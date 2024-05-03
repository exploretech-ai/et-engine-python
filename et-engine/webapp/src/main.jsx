import React from 'react'
import ReactDOM from 'react-dom'
import './index.css'
import App from './App'

import Home from './pages/Home'
import Filesystems from './pages/Filesystems'
import Tools from './pages/Tools'
import Keys from './pages/Keys'
import Jobs from './pages/Jobs'
import Share from './pages/Share'

import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App/>,
    children: [
      {
        path: "/",
        element: <Home/>
      },
      {
        path: "home",
        element: <Home/>
      },
      {
        path: "filesystems",
        element: <Filesystems/>
      },
      {
        path: "tools",
        element: <Tools/>
      },
      {
        path: "keys",
        element: <Keys/>
      },
      {
        path: "jobs",
        element: <Jobs/>
      },
      {
        path: "share",
        element: <Share/>
      }
    ]
  }
]);



ReactDOM.render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
  document.getElementById('root')
)
