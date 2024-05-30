import * as THREE from 'three'


class Colormap {

    /**
     * Creates a Colormap object
     * @param {Array} stops array of THREE.Color
     * @param {boolean} interpolate (named arg) whether to interpolate between colors (default true)
     * @param {function} transform (named arg) function that transforms the values before mapping (default null)
     * @param {Number} minVal (named arg) the minimum value to use for colormapping (default null)
     * @param {Number} maxVal (named arg) the maximum value to use for colormapping (default null)
     */
    constructor(stops, { interpolate=true, transform=null, minVal=null, maxVal=null }) { 
        this.stops = stops
        this.interpolate = interpolate
        this.transform = transform 
        this.minVal = minVal
        this.maxVal = maxVal

        this.nstops = stops.length
        this.name = "custom"
    }

    /**
     * Evaluates the colormap at the given value, returning a THREE.Color object. 
     * The value is transformed into the range [0, 1] by (T(x) - T(xmin)) / (T(xmax) - T(xmin)).
     * @param {Number} value the value to evaluate at
     * @returns a THREE.Color
     */
    eval(value) { 

        // Initialize relevant numbers
        let val = value
        let min = this.minVal
        let max = this.maxVal

        // Return first stop if there is only one color
        if (min === max) {
            return this.stops[0]
        }

        // Transform if a transformation is specified
        if (this.transform !== null) {
            val = this.transform(val)
            min = this.transform(min)
            max = this.transform(max)
        }

        // Scale between 0-1
        val = (val - min) / (max - min)

        // Find the indices of the color stops above and below the value
        const iBelow = Math.floor(val * (this.nstops - 1))
        const iAbove = Math.ceil(val * (this.nstops - 1))

        // Find the associated colors
        const cBelow = this.stops[iBelow]
        const cAbove = this.stops[iAbove]
        
        // Calculate the percentage of the value between the two stops
        let pct = (val * (this.nstops - 1) - iBelow)
        pct = Math.max(0, pct)
        pct = Math.min(1, pct)

        // Interpolate from cBelow -> cAbove using the lerp method
        const color = cBelow.clone()
        color.lerp(cAbove, pct)

        return color
    }

}

/**
 * A pre-defined colormap
 */
class TerrainColormap extends Colormap {
    constructor({ interpolate=true, transform=null, minVal=null, maxVal=null }) {
        const colorStops = []
        colorStops.push(new THREE.Color(0x09B2EB))
        colorStops.push(new THREE.Color(0x94DB65))
        colorStops.push(new THREE.Color(0x6CAD40))
        colorStops.push(new THREE.Color(0x2E8025))
        colorStops.push(new THREE.Color(0xD7F58C))
        colorStops.push(new THREE.Color(0x805B05))
        colorStops.push(new THREE.Color(0xA8A8A8))
        colorStops.push(new THREE.Color(0xE3EEFF))
        colorStops.push(new THREE.Color(0xF2F7FF))

        super(colorStops, {interpolate:interpolate, transform:transform, minVal:minVal, maxVal:maxVal})
        this.name='Terrain'
    }
}

/**
 * A pre-defined colormap
 */
class SeismicColormap extends Colormap {
    constructor({ interpolate=true, transform=null, minVal=null, maxVal=null }) {
        const colorStops = []
        colorStops.push(new THREE.Color('blue'))
        colorStops.push(new THREE.Color('white'))
        colorStops.push(new THREE.Color('red'))

        super(colorStops, {interpolate:interpolate, transform:transform, minVal:minVal, maxVal:maxVal})
        this.name = "Seismic"
    }
}

export {TerrainColormap, SeismicColormap}
export default Colormap