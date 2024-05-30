import * as THREE from 'three'
import { VolumeGeometry } from './geometries/VolumeGeometry'
import { TerrainColormap } from './geometries/Colormaps'
import Layer from './Layer'


class Volume extends Layer {

    /**
     * Creates a Lines object
     * @param {file} file file object associated with the layer
     */
    constructor({vertices, voxels, values}) {

        // Calls the Layer class
        super()
        this.type = "volume"

        this.numVertices = vertices.length
        this.numVoxels = voxels.length

        this.parameters = {
            vertices: vertices,
            voxels: voxels,
            values: values
        }

        this.style = {
            opacity: 1
        }

    }

    /**
     * Loads the data from the CSV, creates the geometry, and sets the material
     */
    async initialize() {
        // await this.parseMesh()
        this.geometry = new VolumeGeometry(this.parameters)
        this.geometry.setColors(TerrainColormap)
        
        this.material = new THREE.MeshLambertMaterial({
            color: 0xFFFFFF,
            emissive: 0x000000,
            side: THREE.DoubleSide,
            vertexColors: true,
            transparent: true,
            opacity: this.opacity
        });
    }

    /**
     * Sets the color attribute given a string field
     * @param {string} field string specifier for the color index
     */
    setColors(colorMap) {
        this.geometry.setColors(colorMap)
    }

    /**
     * Gets the min and max of the CSV at the specified column
     * @param {string} field string specifier for the variable of interest
     * @returns [min, max] values
     */
    getMinMax() {

    }

    

    
}

export default Volume