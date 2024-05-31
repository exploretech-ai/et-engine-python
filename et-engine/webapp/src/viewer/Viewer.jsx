import './Viewer.css';
import React, { useRef, useState } from "react";

import * as THREE from 'three'
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

import Sidebar from './Sidebar';
import Model from './components/Canvas/Model'
import CameraControls from './components/Canvas/CameraControls';


function Viewer({focus, setFocus}) {
  
  const [orbitCenter, setOrbitCenter] = useState(new THREE.Vector3(0,0,0))

  return (
      <div id="content-container">
        <div id="sidebar-container">
          <Sidebar />
        </div>

        <div id="canvas-container">
        <Canvas id="canvas">
          <ambientLight /> 
          <Model setFocus={setFocus}/>
          <CameraControls focus={focus} setOrbitCenter={setOrbitCenter}/>
          <OrbitControls target={orbitCenter}/>
        </Canvas>
        </div>
    </div>
    );
}



export default Viewer;
