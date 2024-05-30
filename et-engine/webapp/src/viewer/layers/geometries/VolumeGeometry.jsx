import * as THREE from 'three'

class VolumeGeometry extends THREE.BufferGeometry {

    /**
     * 
     * @param {Array} vertices array of length N with each element containing a length-3 array with x, y, z coordinates of the point
     * @param {Array} voxels array of length M with each element containing an 8-dimensional array, where each element contains the index of the point in that voxel
     * @param {Array} values array of length N with color values at each vertex 
     */
	constructor({vertices, voxels, values} ) {

        super();
        this.type = 'VolumeGeometry';

        // Assign args to the object 
        this.vertices = vertices
        this.voxels = voxels
        this.values = values

        // Initialize min and max bounds
        this.minVal = 999999
        this.maxVal = -999999

        // Create initial geometry
        this.updateGeometry()
        

    }

    /**
     * Re-calculates the mesh and assigns it to the base class attributes
     */
    updateGeometry() {

        // Initialize the buffer geometry arrays
        const indices = [];
		const vertices = [];
		const normals = [];
		const uvs = [];

        // Loop through each vertex to push them to the indices array
        for (let i = 0; i < this.vertices.length; i++) {

            // Push the vertex points
            const vertex = this.vertices[i]
            vertices.push(vertex[0], vertex[1], vertex[2])

            // Not sure what these do exactly but they are needed to make it work
            normals.push( 0, 0, 1 );
            uvs.push(0, 0)

            // Update the min/max
            if (this.values[i] > this.maxVal) {this.maxVal = this.values[i]}
            if (this.values[i] < this.minVal) {this.minVal = this.values[i]}
        }

        // Loop through each voxel, triangulate each face, and push the indices
        for (let i = 0; i < this.voxels.length; i++) {
            const voxel = this.voxels[i]

            // Bottom face
            indices.push(voxel[0], voxel[1], voxel[2])
            indices.push(voxel[1], voxel[3], voxel[2])

            // // Top face
            indices.push(voxel[4], voxel[5], voxel[6])
            indices.push(voxel[5], voxel[7], voxel[6])

            // // South face
            indices.push(voxel[4], voxel[5], voxel[0])
            indices.push(voxel[5], voxel[1], voxel[0])

            // // North face
            indices.push(voxel[6], voxel[7], voxel[2])
            indices.push(voxel[7], voxel[3], voxel[2])

            // // West face
            indices.push(voxel[0], voxel[2], voxel[4])
            indices.push(voxel[2], voxel[6], voxel[4])

            // // East face
            indices.push(voxel[1], voxel[3], voxel[5])
            indices.push(voxel[3], voxel[7], voxel[5])
        }

        // Set the geometry
        this.setIndex( indices );
		this.setAttribute( 'position', new THREE.Float32BufferAttribute( vertices, 3 ) );
		this.setAttribute( 'normal', new THREE.Float32BufferAttribute( normals, 3 ) );
		this.setAttribute( 'uv', new THREE.Float32BufferAttribute( uvs, 2 ) );
        
    }


    /**
     * Re-calculates colors at each mesh node and sets it as a buffer attribute
     * @param {Colormap} cmap a Colormap object used to set colors
     * @param {struct} colorArgs colormap arguments including minVal and maxVal and transform
     */
    setColors(ColorMap, colorArgs=null) {

        if (colorArgs === null) {
            colorArgs = {minVal: this.minVal, maxVal: this.maxVal}
        }
        const cmap = new ColorMap(colorArgs)

        // Initialize color variables that will be used to set the vertex colors
        const color = new THREE.Color()
        const colors = []

        // Loop through each vertex and assign a color
        for (let i = 0; i < this.vertices.length; i++) {
            // Map elevation to color
            color.setHex(cmap.eval(this.values[i]).getHex())
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



export { VolumeGeometry };