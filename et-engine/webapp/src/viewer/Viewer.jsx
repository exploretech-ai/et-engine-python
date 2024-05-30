import './Viewer.css';
import React, { useRef, useState } from "react";

import * as THREE from 'three'
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

import Sidebar from './Sidebar';
import Model from './components/Canvas/Model'
import CameraControls from './components/Canvas/CameraControls';


function Viewer({focus, setFocus}) {

  // Initialize the camera rotation origin
  
  const [orbitCenter, setOrbitCenter] = useState(new THREE.Vector3(0,0,0))

  // Initialize sidebar, including the sidebar properties
  const sidebar = <Sidebar />
  
  // Load the model using the sidebar properties
  const model = <Model setFocus={setFocus}/>

  // Initialize the canvas with the 3D model
  let canvas = <Canvas id="canvas">
    <ambientLight /> 
    {model}
    <CameraControls focus={focus} setOrbitCenter={setOrbitCenter}/>
    <OrbitControls target={orbitCenter}/>
    
  </Canvas>


  // Returns the sidebar and the canvas
  return (
      <div id="content-container">
        <div id="sidebar-container">
          {sidebar}
        </div>

        <div id="canvas-container">
          {canvas}
        </div>
    </div>
    );
}



export default Viewer;
