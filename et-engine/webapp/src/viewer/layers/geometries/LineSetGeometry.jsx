import * as THREE from 'three'

class LineSetGeometry extends THREE.BufferGeometry {

    /**
     * 
     * @param {Array} points an array of array of point data from a CSV
     * @param {string} xColumn string specified for the column containing the x-coordinates
     * @param {string} yColumn string specified for the column containing the y-coordinates
     * @param {string} zColumn string specified for the column containing the z-coordinates
     * @param {string} lineColumn string specified for the column containing the line ID
     * @param {Number} width width in meters of the line mesh (default = 20)
     */
    // constructor( {xdata, ydata, zdata, linedata, width=20}) {
	constructor( {points, xColumn, yColumn, zColumn, lineColumn, width}) {

        super();
        this.type = 'LineSetGeometry';

        this.points = points
        this.width = width

        // Convert the string specifiers to indices
        this.xIndex = points[0].findIndex((col) => col == xColumn)
        this.yIndex = points[0].findIndex((col) => col == yColumn)
        this.zIndex = points[0].findIndex((col) => col == zColumn)
        this.lineIndex = points[0].findIndex((col) => col == lineColumn)
        this.valIndex = null

        // Create initial geometry
        this.updateGeometry()

    }

    /**
     * Re-calculates the mesh and assigns it to the base class attributes
     */
    updateGeometry() {

        // These are the main geometry attributes
        this.indices = [];
        this.vertices = [];
        this.normals = [];
        this.uvs = [];
    
        // End loop on second-to-last point
        const count = this.points.length-1

        // Iteration parameters
        let i = 1
        let lineID = this.points[i][this.lineIndex]

        // Initialize first line
        this.initializeLine(i)
        i++

        // Main loop to add each line
        while (i < count) {
            this.setMiddlePoint(i)
            
            // Check two points ahead to see if the line needs to be finalized
            if (this.points[i+2][this.lineIndex] != lineID) {
                
                i++
                this.finalizeLine()

                // Skip the end point since it was already finalized and jump to start of next line
                i++
                
                // Make sure we're at the start of a new line & initialize a new line if so
                if (i < count) {

                    lineID = this.points[i][this.lineIndex]
                    this.initializeLine(i)
                }
            }     
            i++
        }

        // Finalize the mesh
        this.setIndex( this.indices );
        this.setAttribute( 'position', new THREE.Float32BufferAttribute( this.vertices, 3 ) );
        this.setAttribute( 'normal', new THREE.Float32BufferAttribute( this.normals, 3 ) );
        this.setAttribute( 'uv', new THREE.Float32BufferAttribute( this.uvs, 2 ) );

    }

    /**
     * Grabs coordinates from the points list at the specified index and returns them as a vector
     * @param {integer} i index to retrieve
     * @returns THREE.Vector3 of the coordinate
     */
    getCoord(i) {
        const x = Number(this.points[i][this.xIndex])
        const y = Number(this.points[i][this.yIndex])
        const z = Number(this.points[i][this.zIndex])

        return new THREE.Vector3(x, y, z)
    }

    /**
     * appends the given point to geometry attributes vertices, normals, and uvs
     * @param {THREE.Vector3} point point to push
     */
    pushPoint(coord) {
        this.vertices.push(coord.x, coord.y, coord.z)
        this.normals.push(0,0,1)
        this.uvs.push(0,1)
    }

    /**
     * Initialize a new line by setting the 3 along-line points and pushing the bounding box for the initial point at index i
     * @param {int} i initializes a new line at this index
     */
    initializeLine(i) {

        // Initial Point starting at index i
        this.p0 = this.getCoord(i)
        this.p1 = this.getCoord(i+1)
        this.p2 = new THREE.Vector3()

        // Computes the edge associated with the initial point
        const dv = new THREE.Vector2(this.p1.x - this.p0.x, this.p1.y - this.p0.y)
        dv.set(dv.y, -dv.x).setLength(this.width)

        // Push these edge points to the list
        this.pushPoint(new THREE.Vector3(this.p0.x + dv.x, this.p0.y + dv.y, this.p0.z))
        this.pushPoint(new THREE.Vector3(this.p0.x - dv.x, this.p0.y - dv.y, this.p0.z))
        
        // Push the associated indices
        const j = (i - 1) * 2
        this.indices.push(j, j+3, j+1)
        this.indices.push(j, j+2, j+3)
    }

    /**
     * Pushes a point in the middle of the line
     * @param {int} i index of point to push
     */
    setMiddlePoint(i) {

        // Grab next coordinate and set it to p2
        const nextCoord = this.getCoord(i+1)
        this.p2.set(nextCoord.x, nextCoord.y, nextCoord.z)

        // Compute vectors pointing from p1->p0 and p1->p2
        const a = new THREE.Vector2(this.p0.x - this.p1.x, this.p0.y - this.p1.y)
        const b = new THREE.Vector2(this.p2.x - this.p1.x, this.p2.y - this.p1.y)

        // Calculate the angle between the vectors and rotate a halfway to b
        const angle = a.angleTo(b) / 2
        a.setLength(this.width).rotateAround(new THREE.Vector2(0,0), angle)

        // Push the edge points
        this.pushPoint(new THREE.Vector3(this.p1.x + a.x, this.p1.y + a.y, this.p1.z))
        this.pushPoint(new THREE.Vector3(this.p1.x - a.x, this.p1.y - a.y, this.p1.z))

        // Update the back two points for the next iteration
        this.p0.set(this.p1.x, this.p1.y, this.p1.z)
        this.p1.set(this.p2.x, this.p2.y, this.p2.z)

        // Push the associated indices for the edge points
        const j = (i - 1) * 2
        this.indices.push(j, j+3, j+1)
        this.indices.push(j, j+2, j+3)
    }

    /**
     * finalizes the line by pushing the last edge
     */
    finalizeLine() { 

        // Calculate vector from p1->p0 (where p1 is at the end of the line)
        const dv = new THREE.Vector3(this.p0.x - this.p1.x, this.p0.y - this.p1.y)

        // Calculate the edges
        dv.set(-dv.y, dv.x).setLength(this.width)

        // Push these last two edge vertices
        this.pushPoint(new THREE.Vector3(this.p1.x + dv.x, this.p1.y + dv.y, this.p1.z))
        this.pushPoint(new THREE.Vector3(this.p1.x - dv.x, this.p1.y - dv.y, this.p1.z))
    }

    /**
     * Re-calculates colors at each mesh node and sets it as a buffer attribute
     * @param {Colormap} cmap a Colormap object used to set colors
     */
    setColors(cmap) {

        // Initialize color variables that will be used to set the vertex colors
        const color = new THREE.Color()
        const colors = []
        const count = this.points.length - 1

        // Loop through each vertex and assign a color
        for (let index = 1; index < count; index++) {

            // Get elevation & normalize
            const val = Number(this.points[index][this.valIndex])

            // Map elevation to color
            color.setHex(cmap.eval(val).getHex())
            colors.push(color.r, color.g, color.b);
            colors.push(color.r, color.g, color.b);
        }

        // Set colors as a new attribute
        this.setAttribute( 'color', new THREE.Float32BufferAttribute(colors, 3));
    }

	copy( source ) {

		super.copy( source );

		this.parameters = Object.assign( {}, source.parameters );

		return this;

	}

}



export { LineSetGeometry };