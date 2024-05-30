import * as THREE from 'three'

/**
 * Modified from the THREE.SphereGeometry source code
 */
class PointGeometry extends THREE.BufferGeometry {

    /**
     * 
     * @param {Array} coords length 3 vector with x, y, z
     * @param {Number} radius radius of the sphere (default 1)
     * @param {Integer} widthSegments number of segments in the phi direction (default 32)
     * @param {Integer} heightSegments number of segments in the theta direction (default 16)
     * @param {Number} phiStart starting phi value, in radians (default 0)
     * @param {Number} phiLength max phi value, in radians (default 2\pi)
     * @param {Number} thetaStart starting theta value, in radians (default 0)
     * @param {Number} thetaLength max theta value, in radians (default \pi)
     */
	constructor( coords, radius = 1, widthSegments = 32, heightSegments = 16, phiStart = 0, phiLength = Math.PI * 2, thetaStart = 0, thetaLength = Math.PI ) {

		super();

		this.type = 'PointGeometry';

        // Geometry parameters
        this.radius = radius
        this.phiStart = phiStart
        this.phiLength = phiLength
        this.thetaStart = thetaStart
        this.thetaLength = thetaLength

        // Initialize segments
		this.widthSegments = Math.max( 3, Math.floor( widthSegments ) );
		this.heightSegments = Math.max( 2, Math.floor( heightSegments ) );
		this.thetaEnd = Math.min( thetaStart + thetaLength, Math.PI );

        // From THREE.SphereGeometry, not sure that they do
		this.index = 0;
		this.grid = [];
		
		// buffers (From THREE.SphereGeometry)
		this.indices = [];
		this.vertices = [];
		this.normals = [];
		this.uvs = [];

        // This method was modified from THREE.SphereGeometry
        this.appendSphere(coords[0], coords[1], coords[2])

        // Set the buffers
		this.setIndex( this.indices );
		this.setAttribute( 'position', new THREE.Float32BufferAttribute( this.vertices, 3 ) );
		this.setAttribute( 'normal', new THREE.Float32BufferAttribute( this.normals, 3 ) );
		this.setAttribute( 'uv', new THREE.Float32BufferAttribute( this.uvs, 2 ) );
	}

    /**
     * Adds a sphere to the buffer at the specified coordinate. This was copied/modified from the THREE.js source code for SphereGeometry.
     * @param {Number} x x-coordinate of the center
     * @param {Number} y y-coordinate of the center
     * @param {Number} z z-coordinate of the center
     */
    appendSphere(x, y, z) {

        // Initialize placeholders
        const vertex = new THREE.Vector3();
		const normal = new THREE.Vector3();
        const indexStart = this.index 

        // Loop through all the heights
        for ( let iy = 0; iy <= this.heightSegments; iy ++ ) {

			const verticesRow = [];

			const v = iy / this.heightSegments;

			// special case for the poles

			let uOffset = 0;

			if ( iy === 0 && this.thetaStart === 0 ) {

				uOffset = 0.5 / this.widthSegments;

			} else if ( iy === this.heightSegments && this.thetaEnd === Math.PI ) {

				uOffset = - 0.5 / this.widthSegments;

			}

			for ( let ix = 0; ix <= this.widthSegments; ix ++ ) {

				const u = ix / this.widthSegments;

				// vertex

				vertex.x = - this.radius * Math.cos( this.phiStart + u * this.phiLength ) * Math.sin( this.thetaStart + v * this.thetaLength );
				vertex.y = this.radius * Math.cos( this.thetaStart + v * this.thetaLength );
				vertex.z = this.radius * Math.sin( this.phiStart + u * this.phiLength ) * Math.sin( this.thetaStart + v * this.thetaLength );

                this.vertices.push( vertex.x + x, vertex.y + y, vertex.z + z );

				// normal

				normal.copy( vertex ).normalize();
				this.normals.push( normal.x, normal.y, normal.z );

				// uv

				this.uvs.push( u + uOffset, 1 - v );

				verticesRow.push( this.index ++ );

			}

			this.grid.push( verticesRow );

		}

		// indices
		for ( let iy = 0; iy < this.heightSegments; iy ++ ) {

			for ( let ix = 0; ix < this.widthSegments; ix ++ ) {

				const a = this.grid[ iy ][ ix + 1 ] + indexStart;
				const b = this.grid[ iy ][ ix ] + indexStart;
				const c = this.grid[ iy + 1 ][ ix ] + indexStart;
				const d = this.grid[ iy + 1 ][ ix + 1 ] + indexStart;
                // console.log(a,b,c,d)

				if ( iy !== 0 || this.thetaStart > 0 ) this.indices.push( a, b, d );
				if ( iy !== this.heightSegments - 1 || this.thetaEnd < Math.PI ) this.indices.push( b, c, d );

			}
		}
    }
}

export { PointGeometry };