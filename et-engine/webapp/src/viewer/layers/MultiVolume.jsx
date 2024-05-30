import * as THREE from 'three'
import { VolumeGeometry } from './geometries/VolumeGeometry'
import Colormap, { TerrainColormap } from './geometries/Colormaps'
import Layer from './Layer'


class MultiVolume extends Layer {

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

        // Holds the unique values for separating meshes by value
        this.uniqueValues = null

        // Colormap style parameters
        this.style = {
            minVal: null,
            maxVal: null
        }
    }

    /**
     * Loads the data from the CSV, creates the geometry, and sets the material
     */
    async initialize() {

        // Load the file

        // Initialize the style and unique values
        this.uniqueValues = this.findUniqueValues()
        this.style.minVal = Math.min(...this.uniqueValues)
        this.style.maxVal = Math.max(...this.uniqueValues)
        
        // Initialize the layer properties
        const materials = []
        const geometries = []

        // Loop through each unique value
        for (const val of this.uniqueValues) {

            // Get the mesh associated with the unique value
            const [vertices, voxels, values] = this.sliceByValue(val)

            const volumeParameters = {
                vertices: vertices,
                voxels: voxels,
                values: values
            }

            // Create the new geometry object with the sub-mesh and set the colors
            const newGeometry = new VolumeGeometry(volumeParameters)
            newGeometry.setColors(TerrainColormap, this.style)

            // Add the new mesh and geometry
            geometries.push(newGeometry)
            materials.push(
                new THREE.MeshStandardMaterial({
                    emissive: 0x000000,
                    side: THREE.DoubleSide,
                    vertexColors: true,
                    transparent: true,
                    opacity: 1
                })
            )
        }

        // Set the layer properties
        this.geometry = geometries
        this.material = materials
    }

    /**
     * Sets the color attribute given a colormap
     * @param {Colormap} colorMap colormap to use
     */
    setColors(colorMap) {

        // Loop through each geometry and set the colors based on the colormap and global style
        for (let i = 0; i < this.geometry.length; i++) {
            this.geometry[i].setColors(colorMap, this.style)
        }
    }

    

    /**
     * Gets the unique values in the `values` array
     * @returns a new array with unique values
     */
    findUniqueValues() {
        
        // Loop through all values (except the last one which is an empty string) TODO: fix the empty string bug
        const uniqueValues = []
        for (let i = 0; i < this.numVertices - 1; i++) {

            // If the value is not in the unique values array, then add it
            if (!uniqueValues.includes(this.parameters.values[i])) {uniqueValues.push(this.parameters.values[i])}
        }

        // Sort the unique values in ascending order
        return uniqueValues.sort((a, b) => a - b)
    }

    /**
     * Extracts a sub-mesh where all vertices are equal to the specified value
     * @param {number} val query value to slice the mesh by
     * @returns a 3D array with [vertices, voxels, and values] for the sub-mesh
     */
    sliceByValue(val) {

        // Initialize new voxels etc
        const newVoxels = []
        const newVertices = []
        const newValues = []

        // Track vertices and id shifts
        const verticesToDelete = []
        const shiftArray = []
        let shiftValue = 0

        // Loop through vertices to find which ones need to be deleted
        for (let i = 0; i < this.numVertices; i++) {

            // Keep vertices with values matching the query value 
            if (this.parameters.values[i] == val) {
                newVertices.push(this.parameters.vertices[i])
                newValues.push(this.parameters.values[i])

            // Track vertices that are being deleted and increment vertex index shift
            } else {
                verticesToDelete.push(i)
                shiftValue++     
            }

            // This array tracks the vertex index shift based on the number of vertices deleted
            shiftArray.push(shiftValue)
        }

        // Loop through voxels to shift vertex indices and delete voxels without query value
        for (let i = 0; i < this.numVoxels; i++) {

            // These are used to modify the voxels
            let keepVoxel = true
            const shiftedVoxel = []

            // Loop through all 8 vertex indices in the voxel
            for (let j = 0; j < 8; j++) {

                // Shift vertex index
                const vertexID = this.parameters.voxels[i][j]
                shiftedVoxel.push(vertexID - shiftArray[vertexID])

                // If any vertex matches the list of vertices to delete, then we will not keep this voxel
                if (verticesToDelete.includes(this.parameters.voxels[i][j])) {
                    keepVoxel = false
                }
            }

            // Only keep voxels with all vertices containing the query value
            if (keepVoxel) {
                newVoxels.push(shiftedVoxel)
            }
        }

        return [newVertices, newVoxels, newValues]
    }
}

export default MultiVolume