import * as THREE from 'three'

/**
 * Base Layer class that contains common methods
 */
class Layer {
    /**
     * Creates a base Layer object with a geometry, a material, and a scene.
     * @param {file} file file object attached to the layer
     */
    constructor() {
        
        this.geometry = null
        this.material = null
        this.scene = null
    }

    /**
     * Updates the scene given the geometry and material
     */
    setScene() {

        // Initialize a new scene
        const scene = new THREE.Scene()

        // If the geometry is an array then we will loop through it
        if (Array.isArray(this.geometry)) {

            for (let i = 0; i < this.geometry.length; i++) {
                const mesh = new THREE.Mesh( this.geometry[i], this.material[i] )   
                scene.add(mesh)
            }

        // If the geometry is not an array then we will add the mesh to the scene
        } else {

            const mesh = new THREE.Mesh( this.geometry, this.material )   
            scene.add(mesh)

        }
        
        // Return the scene
        this.scene = scene
    }
}

export default Layer