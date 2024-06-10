import * as THREE from 'three'
import { PointGeometry } from './PointGeometry';


class PointSetGeometry extends THREE.BufferGeometry {

	constructor({points, xColumn, yColumn, zColumn, radius = 100, widthSegments = 32, heightSegments = 16, phiStart = 0, phiLength = Math.PI * 2, thetaStart = 0, thetaLength = Math.PI} = {}) {
		
		super()
		this.type = 'PointSetGeometry';

		this.xIndex = points[0].findIndex((col) => col == xColumn)
        this.yIndex = points[0].findIndex((col) => col == yColumn)
        this.zIndex = points[0].findIndex((col) => col == zColumn)

		this.valIndex = 0

		this.points = points

		// const point0 = [x[0], y[0], z[0]]
		// super(point0, radius, widthSegments, heightSegments, phiStart, phiLength, thetaStart, thetaLength);

		this.radius = radius
		this.widthSegments = widthSegments
		this.heightSegments = heightSegments
		this.phiStart = phiStart
		this.phiLength = phiLength
		this.thetaStart = thetaStart
		this.thetaLength = thetaLength

		this.updateGeometry()


	}

	updateGeometry() {

		// From THREE.SphereGeometry, not sure that they do
		this.index = 0;
		this.grid = [];

		// buffers (From THREE.SphereGeometry)
		this.indices = [];
		this.vertices = [];
		this.normals = [];
		this.uvs = [];

		// generate vertices, normals and uvs
        for (let i = 1; i < this.points.length; i++) {
			const x = Number(this.points[i][this.xIndex])
			const y = Number(this.points[i][this.yIndex])
			const z = Number(this.points[i][this.zIndex])
            this.appendSphere(x, y, z)
        }
		
		// build geometry
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

}

export { PointSetGeometry };