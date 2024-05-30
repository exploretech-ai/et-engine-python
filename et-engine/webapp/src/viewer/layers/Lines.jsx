import * as THREE from 'three'
import { LineSetGeometry } from './geometries/LineSetGeometry'
import { SeismicColormap } from './geometries/Colormaps';
import Layer from './Layer'


class Lines extends Layer {

    /**
     * Creates a Lines object
     * @param {file} file file object associated with the layer
     */
    constructor({points, fields, xColumn, yColumn, zColumn, lineColumn}) {

        // Calls the Layer class
        super()
        this.type = "Lines"
        
        this.parameters = {
            xColumn: xColumn,
            yColumn: yColumn,
            zColumn: zColumn,
            lineColumn: lineColumn,
            points: points,
            fields: fields
        }

        // These are used elsewhere

        // These parameters control the styling
        this.style = {
            colorValue: null,
            minVal: null,
            maxVal: null,
            transform: null,
            width: 50,
            alpha: 1,
            colorMap: SeismicColormap
        }
    }

    /**
     * Loads the data from the CSV, creates the geometry, and sets the material
     */
    async initialize() {
        // this.data = await this.parseCSV()
        this.geometry = new LineSetGeometry({...this.parameters, width: this.style.width})
        this.material = new THREE.MeshLambertMaterial({
            color: 0xFFFFFF,
            emissive: 0x000000,
            side: THREE.DoubleSide,
            vertexColors: true
        });
    }

    /**
     * Sets the color attribute given a string field
     * @param {string} field string specifier for the color index
     */
    setColors(field) {

        // Get the min and max of the field
        const [minVal, maxVal] = this.getMinMax(field)

        // Set the colormap args and then the colormap
        const colorArgs = {
            minVal: minVal, 
            maxVal: maxVal, 
            transform: this.style.transform
        }
        const cmap = new this.style.colorMap(colorArgs)

        // Set the field index in the LineSetGeometry and then use it to update the colors
        this.geometry.valIndex = this.parameters.points[0].findIndex((col) => col == field)
        this.geometry.setColors(cmap)
    }

    /**
     * Gets the min and max of the CSV at the specified column
     * @param {string} field string specifier for the variable of interest
     * @returns [min, max] values
     */
    getMinMax(field) {

        // Get the index of the field
        const valIndex = this.parameters.points[0].findIndex((col) => col == field)

        // Initialize min and max
        let minVal = Number(this.parameters.points[1][valIndex])
        let maxVal = minVal

        // Iterate through all the data and set min and max accordingly
        for (let i=2; i < this.parameters.points.length; i++) {
            const val = Number(this.parameters.points[i][valIndex])
            if (val > maxVal) maxVal = val
            if (val < minVal) minVal = val
        }
        return [minVal, maxVal]
    }

}

export default Lines