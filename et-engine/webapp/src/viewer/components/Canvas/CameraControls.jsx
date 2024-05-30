import { useThree } from '@react-three/fiber'
import { useEffect } from "react";
import * as THREE from 'three'


/**
 * 
 * @param {state} focus the checkbox props to focus on
 * @param {setState} setOrbitCenter the state setter associated with the orbit controls target 
 */
function CameraControls({ focus, setOrbitCenter }) {

    // This will be used for setting the new camera
    const state = useThree()
  
    // Runs each time focus is updated
    useEffect(() => {
      if (focus !== null) {
  
        // Update the orbit center
        const newCenter = updateOrbitCenter()
  
        // Update the camera to new focus
        updateCamera(newCenter)
  
      }
    }, [focus])
  
    // This function sets the new camera position given the updated center
    function updateCamera(newCenter) {
  
        // Initialize a new camera
        const fov = 55 
        const newCamera = new THREE.PerspectiveCamera()
        newCamera.fov = fov
  
        // Calculate the camera position by fitting the bounding box to the screen
        const boundingBox = focus.object.scene.children[0].geometry.boundingBox
        const width = boundingBox.max.x - boundingBox.min.x
        const height = boundingBox.max.y - boundingBox.min.y
  
        const alpha = fov * Math.PI / 180
        const zoomFactor = 1 / (2 * Math.tan(alpha / 2))
        const dz = Math.max(width, height) * zoomFactor
  
        // Set the new camera position at a birds-eye view
        newCamera.position.set(newCenter.x, newCenter.y, newCenter.z  + dz)
    
        // Look at the orbit center
        newCamera.lookAt(newCenter)
  
        // Really big far plane 
        newCamera.far = dz * 10
  
        // Needs to run each time the camera parameters are changed
        newCamera.updateProjectionMatrix()
        
        // Finally, set the new camera
        state.set({ camera: newCamera })
  
    }
  
    // This function calculates and sets the orbit controls target
    function updateOrbitCenter() {
  
        // Update bounding box
        focus.object.scene.children[0].geometry.computeBoundingBox();
  
        // Put bounding box center into a Vector3
        const boundingBox = focus.object.scene.children[0].geometry.boundingBox
        const center = new THREE.Vector3()
        boundingBox.getCenter(center)
  
        // Set the new orbit center to the bounding box center
        setOrbitCenter(center)
  
        return center
  
    }
  
  }

  export default CameraControls