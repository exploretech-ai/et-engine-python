import * as THREE from 'three'


class DrillholeGeometry extends THREE.BufferGeometry {

	constructor({collar, dip, dipDirection, length , tubularSegments = 64, radius = 25, radialSegments = 8, closed = true} = {} ) {

		super();

		this.type = 'DrillholeGeometry';

        const path = new DrillholePath(collar, dip, dipDirection, length)

		this.parameters = {
			path: path,
			tubularSegments: tubularSegments,
			radius: radius,
			radialSegments: radialSegments,
			closed: closed
		};

		const frames = path.computeFrenetFrames( tubularSegments, closed );

		// expose internals

		this.tangents = frames.tangents;
		this.normals = frames.normals;
		this.binormals = frames.binormals;

		// helper variables

		const vertex = new THREE.Vector3();
		const normal = new THREE.Vector3();
		const uv = new THREE.Vector2();
		let P = new THREE.Vector3();

		// buffer

		const vertices = [];
		const normals = [];
		const uvs = [];
		const indices = [];

		// create buffer data

		generateBufferData();

		// build geometry

		this.setIndex( indices );
		this.setAttribute( 'position', new THREE.Float32BufferAttribute( vertices, 3 ) );
		this.setAttribute( 'normal', new THREE.Float32BufferAttribute( normals, 3 ) );
		this.setAttribute( 'uv', new THREE.Float32BufferAttribute( uvs, 2 ) );

		// functions

		function generateBufferData() {

			for ( let i = 0; i < tubularSegments; i ++ ) {

				generateSegment( i );

			}

			// if the geometry is not closed, generate the last row of vertices and normals
			// at the regular position on the given path
			//
			// if the geometry is closed, duplicate the first row of vertices and normals (uvs will differ)

			generateSegment( ( closed === false ) ? tubularSegments : 0 );

			// uvs are generated in a separate function.
			// this makes it easy compute correct values for closed geometries

			generateUVs();

			// finally create faces

			generateIndices();

		}

		function generateSegment( i ) {

			// we use getPointAt to sample evenly distributed points from the given path

			P = path.getPointAt( i / tubularSegments, P );

			// retrieve corresponding normal and binormal

			const N = frames.normals[ i ];
			const B = frames.binormals[ i ];

			// generate normals and vertices for the current segment

			for ( let j = 0; j <= radialSegments; j ++ ) {

				const v = j / radialSegments * Math.PI * 2;

				const sin = Math.sin( v );
				const cos = - Math.cos( v );

				// normal

				normal.x = ( cos * N.x + sin * B.x );
				normal.y = ( cos * N.y + sin * B.y );
				normal.z = ( cos * N.z + sin * B.z );
				normal.normalize();

				normals.push( normal.x, normal.y, normal.z );

				// vertex

				vertex.x = P.x + radius * normal.x;
				vertex.y = P.y + radius * normal.y;
				vertex.z = P.z + radius * normal.z;

				vertices.push( vertex.x, vertex.y, vertex.z );

			}

		}

		function generateIndices() {

			for ( let j = 1; j <= tubularSegments; j ++ ) {

				for ( let i = 1; i <= radialSegments; i ++ ) {

					const a = ( radialSegments + 1 ) * ( j - 1 ) + ( i - 1 );
					const b = ( radialSegments + 1 ) * j + ( i - 1 );
					const c = ( radialSegments + 1 ) * j + i;
					const d = ( radialSegments + 1 ) * ( j - 1 ) + i;

					// faces

					indices.push( a, b, d );
					indices.push( b, c, d );

				}

			}

		}

		function generateUVs() {

			for ( let i = 0; i <= tubularSegments; i ++ ) {

				for ( let j = 0; j <= radialSegments; j ++ ) {

					uv.x = i / tubularSegments;
					uv.y = j / radialSegments;

					uvs.push( uv.x, uv.y );

				}

			}

		}

	}

    setColors(ColorMap, colorArray, colorArgs=null) {

        if (colorArgs === null) {
            colorArgs = {minVal: this.minVal, maxVal: this.maxVal}
        }
        const cmap = new ColorMap(colorArgs)

        // Initialize color variables that will be used to set the vertex colors
        const color = new THREE.Color()
        const colors = []

        const radialSegments = this.parameters.radialSegments

        function assignColor( i ) {
            color.setHex(cmap.eval(colorArray[i]).getHex())

            for (let j = 0; j <= radialSegments; j++) {
                colors.push(color.r, color.g, color.b);
            }
        }

        for (let i = 0; i < this.parameters.tubularSegments; i++) {
            assignColor( i )
        }

        assignColor( (this.parameters.closed === false) ? this.parameters.tubularSegments: 0 )

        this.setAttribute( 'color', new THREE.Float32BufferAttribute(colors, 3));
    }

}


/**
 * Linear drillhole path
 */
class DrillholePath extends THREE.Curve {

    /**
     * 
     * @param {Array} collar length 3 array with x, y, z
     * @param {Number} dip dip angle below the horizon, in degrees
     * @param {Number} dipDirection dip direction in degrees clockwise from north
     * @param {Number} length length of the drillhole
     */
    constructor(collar, dip, dipDirection, length){

        super()
        this.collar = collar
        this.dip = dip
        this.dipDirection = dipDirection
        this.length = length
    }

    /**
     * Overrides the THREE.Curve 
     * @param {Number} t value between 0 and 1 along the curve
     * @param {*} optionalTarget 
     * @returns 
     */
    getPoint(t, optionalTarget = new THREE.Vector3()) {

        // Radians conversion
        const theta = this.dipDirection * Math.PI / 180
        const phi = this.dip * Math.PI / 180

        // Convert t to depth along drillhole
        const depth = t * this.length

        // x, y, z offsets based on drilling orientation
        const dx = depth * Math.cos(phi) * Math.sin(theta)
        const dy = depth * Math.cos(phi) * Math.cos(theta)
        const dz = -1 * depth * Math.sin(phi)

        // Calculate position
        const x = this.collar[0] + dx
        const y = this.collar[1] + dy
        const z = this.collar[2] + dz

        return optionalTarget.set(x, y, z)
    }
}

export { DrillholeGeometry };