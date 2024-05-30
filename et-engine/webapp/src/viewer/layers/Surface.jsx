import * as THREE from 'three'
import { DEMGeometry } from "./geometries/DEMGeometry";
import Layer from './Layer'
import { TerrainColormap } from './geometries/Colormaps'

class Surface extends Layer {
    /**
     * Creates a surface DEM object
     * @param {object literal} parameters object literal containing the parameters needed for initialization
     */
    constructor({origin, resolution, data, noData, nBands, elevationBand, colorBand, height, width}) {
        super()
        this.parameters = {
            origin: origin,
            resolution: resolution,
            data: data,
            noData: noData,
            nBands: nBands,
            elevationBand: elevationBand,
            colorBand: colorBand,
            height: height,
            width: width
        }
        this.type = "Surface"

        this.style = {
            opacity: 1,
            colorMap: TerrainColormap
        }
    }

    /**
     * Creates the geometry and the mesh for the DEM
     */
    async initialize() {
 
        this.geometry = new DEMGeometry(this.parameters)
        this.geometry.setColors(this.style.colorMap)
 
        // Initialize the material
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

}


export default Surface