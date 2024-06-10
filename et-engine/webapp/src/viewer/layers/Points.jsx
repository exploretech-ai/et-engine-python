import * as THREE from 'three'
import Layer from './Layer'
import { TerrainColormap } from './geometries/Colormaps'
import { PointSetGeometry } from './geometries/PointSetGeometry'

class Points extends Layer {
    constructor({points, fields, xColumn, yColumn, zColumn, noData}) {
        super()
        this.parameters = {
            xColumn: xColumn,
            yColumn: yColumn,
            zColumn: zColumn,
            noData: noData,
            points: points,
            fields: fields
        }

        this.type = "Points"

        this.style = {
            opacity: 1,
            colorValue: null,
            minVal: null,
            maxVal: null,
            transform: null,
            colorMap: TerrainColormap,
            radius: 100
        }
    }

    async initialize() {

        this.geometry = new PointSetGeometry({...this.parameters, radius: this.style.radius})
        
        this.material = new THREE.MeshLambertMaterial({
            color: 0xFFFFFF,
            emissive: 0x000000,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: this.style.opacity,
            vertexColors: true
        });
    }

    setOpacity(opacity) {
        this.style.opacity = opacity
        this.material.opacity = opacity
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
        this.geometry.valIndex = this.parameters.fields.findIndex((col) => col == field)
        this.geometry.setColors(cmap)
    }

    /**
     * Gets the min and max of the CSV at the specified column
     * @param {string} field string specifier for the variable of interest
     * @returns [min, max] values
     */
    getMinMax(field) {

        // Get the index of the field
        const valIndex = this.parameters.fields.findIndex((col) => col == field)

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

export default Points