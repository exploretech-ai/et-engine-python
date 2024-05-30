import MultiVolume from './MultiVolume'
import Layer from './Layer'
import Colormap, { SeismicColormap } from './geometries/Colormaps'

class Ensemble extends Layer {

    /**
     * Creates a Lines object
     * @param {FileList} file FileList object associated with the layer
     */
    constructor({realizationParameters, fileNames}) {

        // Calls the Layer class
        super()
        this.type = "Ensemble"

        // Hold MultiVolumes in here and track the number of meshes in each
        this.numRealizations = realizationParameters.length

        this.realizations = []
        this.uniqueValues = []
        this.numMeshes = []

        this.parameters = {
            realizationParameters: realizationParameters,
            fileNames: fileNames
        }
        
        // Global colormap args
        this.style = {
            minVal: 999999,
            maxVal: -999999,
            colorMap: SeismicColormap
        }

        // Tracks which realization has visible=true
        this.currentlyVisible = 0
    }


    /**
     * Load the MultiVolumes 
     */
    async initialize() {

        // Holds all the meshes and geometries
        const geometries = []
        const materials = []

        // Loop through all the files and load them as MultiVolume objects
        for (let i = 0; i < this.numRealizations; i++) {

            const realization = new MultiVolume(this.parameters.realizationParameters[i])
            await realization.initialize()

            this.numMeshes.push(realization.geometry.length)
   
            // Find global min and max for colormap args
            const min = realization.style.minVal
            const max = realization.style.maxVal
            if (min < this.style.minVal) {this.style.minVal = min}
            if (max > this.style.maxVal) {this.style.maxVal = max}

            // Loop through all the geometries and append them to this parent geometry
            for (let j = 0; j < realization.geometry.length; j++) {

                // Check if this unique value is new and save if it is
                if (! this.uniqueValues.includes(realization.uniqueValues[j])) {
                    this.uniqueValues.push(realization.uniqueValues[j])
                }
                this.realizations.push(realization)
                geometries.push(realization.geometry[j])
                materials.push(realization.material[j])

            }
        }

        // Finalize the base geometry and material
        this.geometry = geometries
        this.material = materials
    }

    /**
     * Sets the color attribute for all meshes given a a colormap
     * @param {Colormap} colorMap colormap option
     */
    setColors(colorMap) {

        // Loop through all geometries and set their colors according to the colormap and global min/max
        for (let i = 0; i < this.geometry.length; i++) {
            this.geometry[i].setColors(colorMap, this.style)
        }
    }

    /**
     * Sets the specified realization as visible and all other realizations as invisible
     * @param {int} i integer specifying which realization to set as visible 
     */
    setVisible(i) {

        // Reset this global parameter
        this.currentlyVisible = i

        // This is an index incrementer that is used to help traverse the geometry arrays
        let k0 = 0

        // Loop through all the realizations
        for (let j = 0; j < this.numRealizations; j++) {

            // The default for all realizations is invisible
            let isVisible = false

            // Only switch the visibility if this is specified as the visible realization
            if (j == i) {isVisible = true} 

            // Loop through all the meshes in this realization
            for (let k = k0; k < k0 + this.numMeshes[j]; k++) {

                // Only set the material as visible if the opacity is above the threshold
                if (this.material[k].opacity >= 0.02) {
                    this.scene.children[k].visible = isVisible
                }
            }

            // Increment this index starting position parameter
            k0 += this.numMeshes[j]
        }        
    }

    /**
     * Sets the opacity for all meshes associated with the value 
     * @param {Number} value all unique values matching this value will have their opacity changed 
     * @param {Number} opacity opacity value, between 0 and 1
     */
    setOpacity(value, opacity) {

        // Initialize the index incrementer
        let k0 = 0

        // Loop through all the realizations
        for (let i = 0; i < this.numRealizations; i++) {

            // Loop through all the meshes in this realization
            for (let j = 0; j < this.numMeshes[i]; j++) {

                // Set the geometry index for this realization + mesh number
                const k = j + k0

                // If the unique value of this geometry matches the specified value, then we will change the opacity
                if (this.realizations[i].uniqueValues[j] == value) {

                    // Set the opacity
                    this.material[k].opacity = opacity

                    // If the opacity is very low, then set the entire mesh as invisible
                    if (opacity >= 0.02 & i == this.currentlyVisible) {
                        this.scene.children[k].visible = true
                    } else {
                        this.scene.children[k].visible = false
                        
                    }
                }
            }

            // Increment this index base
            k0 += this.numMeshes[i]
        }
    }

    /**
     * Alters the setScene method to ensure the first realization is displayed on load.
     */
    setScene() {
        super.setScene()
        this.setVisible(0)
    }
    
}

export default Ensemble