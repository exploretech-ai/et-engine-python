import React from 'react'
import ReactDOM from 'react-dom'
import './index.css'
import App from './App'

import Home from './pages/Home'
import Filesystems from './pages/Filesystems'
import Tools from './pages/Tools'
import Keys from './pages/Keys'
import Tasks from './pages/Tasks'
import Viewer from './pages/Viewer'

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
        path: "tasks",
        element: <Tasks/>
      },
      {
        path: "viewer",
        element: <Viewer/>
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
