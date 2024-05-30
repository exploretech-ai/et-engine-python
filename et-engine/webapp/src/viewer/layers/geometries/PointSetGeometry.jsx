import * as THREE from 'three'
import { PointGeometry } from './PointGeometry';


class PointSetGeometry extends PointGeometry {

	constructor( x, y, z, radius = 1, widthSegments = 32, heightSegments = 16, phiStart = 0, phiLength = Math.PI * 2, thetaStart = 0, thetaLength = Math.PI ) {

		const point0 = [x[0], y[0], z[0]]
		super(point0, radius, widthSegments, heightSegments, phiStart, phiLength, thetaStart, thetaLength);

		this.type = 'PointSetGeometry';

		// generate vertices, normals and uvs
        for (let i = 1; i < x.length; i++) {
            super.appendSphere(x[i], y[i], z[i])
        }
		
		// build geometry
		this.setIndex( this.indices );
		this.setAttribute( 'position', new THREE.Float32BufferAttribute( this.vertices, 3 ) );
		this.setAttribute( 'normal', new THREE.Float32BufferAttribute( this.normals, 3 ) );
		this.setAttribute( 'uv', new THREE.Float32BufferAttribute( this.uvs, 2 ) );

	}

}

export { PointSetGeometry };