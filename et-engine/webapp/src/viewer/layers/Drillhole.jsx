import * as THREE from 'three'
import Layer from './Layer'
import { PointGeometry } from './geometries/PointGeometry'
import { SeismicColormap } from './geometries/Colormaps'
import { DrillholeGeometry } from './geometries/DrillholeGeometry'

class Drillhole extends Layer {
    /**
     * Creates a surface DEM object
     * @param {file} file file object, e.g. from `file = document.getElementById("fileInput").files[0]`
     */
    constructor({collar, dip, dipDirection, length, numIntervals, numObservations, intervals, observations}) {
        super()

        this.type = "Drillhole"

        // Drillhole parameters
        this.parameters = {
            numIntervals: numIntervals,
            numObservations: numObservations,
            intervals: intervals,
            observations: observations,
            collar: collar,
            dip: dip,
            dipDirection: dipDirection,
            length: length
        }
        this.currentObservation = 0
        this.uniqueValues = null

        // Style/visualization parameters
        this.radius = {
            tube: 25,
            sphere: 50
        }

        this.sphereColor = 0x000000

        this.colorArgs = {
            minVal: 0,
            maxVal: 2
        }
    }

    /**
     * Creates a tube for the drillhole and a sphere for the collar
     */
    async initialize() {

        // Drillhole
        const tube = new DrillholeGeometry(this.parameters)
        

        tube.setColors(SeismicColormap, this.parameters.observations[0], this.colorArgs)

        // Collar
        const sphere = new PointGeometry(this.parameters.collar, this.radius.sphere)

        this.geometry = [tube, sphere]
        

        this.material = [
            new THREE.MeshLambertMaterial({
                color: 0xFFFFFF,
                emissive: 0x000000,
                transparent: true,
                opacity: 1,
                vertexColors: true
            }),
            new THREE.MeshLambertMaterial({
                color: this.sphereColor,
                transparent: true,
                opacity: 1
            })
        ]

    }

    setColors(Colormap) {
        this.geometry[0].setColors(Colormap, this.parameters.observations[this.currentObservation], this.colorArgs)
    }

    // DOES NOT WORK
    setTube() {
        // Drillhole
        const tube = new DrillholeGeometry(this.collar, this.dip, this.dipDirection, this.length,
            this.numIntervals, this.radius.tube, 8, true
        )
        tube.setColors(SeismicColormap, this.observations[this.currentObservation], this.colorArgs)

        this.scene.children[0] = tube

    }

    // DOES NOT WORK
    setSphere() {
        const sphere = new PointGeometry(this.collar, this.radius.sphere)
        this.geometry[1] = sphere
    }
    

}


export default Drillhole