import * as THREE from 'three'
import Layer from './Layer'
import { TerrainColormap } from './geometries/Colormaps'
import { PointSetGeometry } from './geometries/PointSetGeometry'

class Points extends Layer {
    constructor({points, fields, xColumn, yColumn, zColumn}) {
        super()
        this.parameters = {
            xColumn: xColumn,
            yColumn: yColumn,
            zColumn: zColumn,
            points: points,
            fields: fields
        }

        this.type = "Points"

        this.style = {
            opacity: 1,
            colorMap: TerrainColormap
        }
    }

    async initialize() {

        this.geometry = new PointSetGeometry(this.parameters)
        
        this.material = new THREE.MeshLambertMaterial({
            color: 0xFFFFFF,
            emissive: 0x000000,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: this.style.opacity,
            vertexColors: true
        });
    }
}

export default Points