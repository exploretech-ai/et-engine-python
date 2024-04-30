import React from 'react'
import ReactDOM from 'react-dom'
import './index.css'
import App from './App'
import Home from './pages/home'
import Filesystems from './pages/Filesystems'
import Tools from './pages/Tools'


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
