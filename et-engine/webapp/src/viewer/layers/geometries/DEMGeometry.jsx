import * as THREE from 'three'

class DEMGeometry extends THREE.BufferGeometry {

    /** 
     *  Creates a DEM surface from geotiff data.
     *  Each grid cell is represented as a vertex and each grid cell is split into two triangles, as shown before.
     *  
     *   (ix, iy)             (ix+1, iy) 
     *           (a) ----- (d)
     *            |       / |
     *            | (ix,iy) |
     *            | /       |
     *           (b) ----- (c)
     * (ix, iy+1)             (ix+1, iy+1)  
     * 
     * This diagram assumes the origin is at top-left corner. Note the cell division is between b-d.
     * 
     * @param {Float32Array} data result from geotiff.js image.readRasters({ interleave: true })
     * @param {number} noData (named argument) no-data value (default = -32767)
     * @param {Array} origin (named argument) list with 2 elements specifying x and y coords of the bottom left corner
     * @param {Array} resolution (named argument)list with 2 elements specifying the cell size in x and y directions
     *   
    */
	constructor({data=null, noData=-32767, origin=[0,0], resolution=[1,1], nBands=1, elevationBand=1, colorBand=1, height, width} = {}) {

		super();

		this.type = 'DEMGeometry';

        // Set raster parameters
        // const {width, height} = data
        const widthSegments = width - 1
        const heightSegments = height - 1
		this.parameters = {
			width: width,
			height: height,
			widthSegments: widthSegments,
			heightSegments: heightSegments,
            origin: origin,
            resolution: resolution,
            noDataValue: noData,
            data: data,
            nBands: nBands,
            elevationBand: elevationBand,
            colorBand: colorBand
		};

        // Calculate number of grid cells for iteration
		const gridX = Math.floor( widthSegments );
		const gridY = Math.floor( heightSegments );

		const gridX1 = gridX + 1;
		const gridY1 = gridY + 1;

        this.gridX1 = gridX1
        this.gridY1 = gridY1

		// Initialize geometry attributes that will be set later
		const indices = [];
		const vertices = [];
		const normals = [];
		const uvs = [];

        // Initialize parameters that will be used for tracking no-data vertices
        const indexShift = []
        let indexCount = 0

        // // Initialize min & max elevation
        this.maxElev = -9999999
        this.minElev = 9999999

        // Loop to create Vertices
		for ( let iy = 0; iy < gridY1; iy ++ ) {

            // y-coordinate
            const y = iy * this.parameters.resolution[1] + this.parameters.origin[1]

			for ( let ix = 0; ix < gridX1; ix ++ ) {

                // x-coordinate
                const x = ix * this.parameters.resolution[0] + this.parameters.origin[0]

                // flat index computed from i,j indices
                const index = (ix + gridX1 * iy) * this.parameters.nBands + this.parameters.elevationBand - 1;

                // Get elevation from raster
                let elev = this.parameters.data[index]

                // If the elevation is not a no-data value, then push the vertex
                if (elev != this.parameters.noDataValue) {

                    // Set min & max for color computation later
                    if (elev > this.maxElev) {this.maxElev = elev}
                    if (elev < this.minElev) {this.minElev = elev}

                    // Push everything
                    vertices.push( x, y, elev );
                    normals.push( 0, 0, 1 );
                    uvs.push( ix / gridX );
                    uvs.push( 1 - ( iy / gridY ) );
                    
                    // Update index trackers
                    indexShift.push(indexCount)
                    indexCount++

                // If the elevation is a no-data value, then mark the index with a -1
                } else {
                    indexShift.push(-1)
                }
			}
		}

        // For-loop for setting cell indices
		for ( let iy = 0; iy < gridY; iy ++ ) {
			for ( let ix = 0; ix < gridX; ix ++ ) {
    
                // Calculate corners (see constructor docs for details)
				const a = ix + gridX1 * iy;                  
				const b = ix + gridX1 * ( iy + 1 );          
				const c = ( ix + 1 ) + gridX1 * ( iy + 1 );  
				const d = ( ix + 1 ) + gridX1 * iy;

                // Shift indices based on no-data values
                const aShift = indexShift[a]
                const bShift = indexShift[b]
                const cShift = indexShift[c]
                const dShift = indexShift[d]

                // Push cells where all vertices have valid data
                if (aShift != -1 & bShift != -1 & dShift != -1) {indices.push( aShift, bShift, dShift )}
                if (bShift != -1 & cShift != -1 & dShift != -1) {indices.push( bShift, cShift, dShift )}
			}
		}

        // Set geometry attributes
		this.setIndex( indices );
		this.setAttribute( 'position', new THREE.Float32BufferAttribute( vertices, 3 ) );
		this.setAttribute( 'normal', new THREE.Float32BufferAttribute( normals, 3 ) );
		this.setAttribute( 'uv', new THREE.Float32BufferAttribute( uvs, 2 ) );
        // this.setColors()

	}

    /**
     * Calculates colors for each cell and sets it as a geometry attribute
     * @param {Colormap} ColorMap a Colormap object that sets the colors 
     */
    setColors(ColorMap) {
   
        // Import a terrain colormap
        const [minVal, maxVal] = this.getMinMax(this.parameters.colorBand)

        const colorArgs = {minVal: minVal, maxVal: maxVal}
        const cmap = new ColorMap(colorArgs)

        // Initialize color variables that will be used to set the vertex colors
        const color = new THREE.Color()
        const colors = []

        // Loop to create Vertices
		for ( let iy = 0; iy < this.gridY1; iy ++ ) {

            // y-coordinate
            const y = iy * this.parameters.resolution[1] + this.parameters.origin[1]

			for ( let ix = 0; ix < this.gridX1; ix ++ ) {

                // x-coordinate
                const x = ix * this.parameters.resolution[0] + this.parameters.origin[0]

                // flat index computed from i,j indices
                
                const elevIndex =  (ix + this.gridX1 * iy) * this.parameters.nBands + this.parameters.elevationBand - 1;

                // Get elevation from raster
                let elev = this.parameters.data[elevIndex]
                
                // If the elevation is not a no-data value, then push the vertex
                if (elev != this.parameters.noDataValue) {
                    const valueIndex = (ix + this.gridX1 * iy) * this.parameters.nBands + this.parameters.colorBand - 1;
                    const value = this.parameters.data[valueIndex]

                    // Map elevation to color
                    color.setHex(cmap.eval(value).getHex())
                    colors.push(color.r, color.g, color.b);
                }
			}
		}

        // Set colors as a new attribute
        this.setAttribute( 'color', new THREE.Float32BufferAttribute(colors, 3));
    }

    getMinMax(band) {

        let minVal = 9999999
        let maxVal = -9999999

        for (let i = band-1; i < this.parameters.data.length; i+=this.parameters.nBands) {
      
          if (this.parameters.data[i] < minVal & this.parameters.data[i] !== this.parameters.noDataValue) {minVal = this.parameters.data[i]}
          if (this.parameters.data[i] > maxVal & this.parameters.data[i] !== this.parameters.noDataValue) {maxVal = this.parameters.data[i]}
      
        }
      
        return([minVal, maxVal])
      }



	copy( source ) {

		super.copy( source );

		this.parameters = Object.assign( {}, source.parameters );

		return this;

	}

	static fromJSON( data ) {

		return new DEMGeometry( data );

	}

}

export { DEMGeometry };