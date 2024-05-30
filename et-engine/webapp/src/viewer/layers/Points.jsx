import * as THREE from 'three'
import { PointSetGeometry } from './geometries/PointSetGeometry'

class Points {
    constructor(file) {
        this.file = file
        this.xColumn = "x_27"
        this.yColumn = "y_27"
        this.zColumn = "altitude"
    }

    async exportScene() {

        const points = await this.parseCSV()

        const scene = new THREE.Scene()

        const geometry = new PointSetGeometry(points, this.xColumn, this.yColumn, this.zColumn, 10)

        const material = new THREE.MeshBasicMaterial( { color: 0xffff00 } ); 
        const sphere = new THREE.Mesh( geometry, material ); 
        
        scene.add(sphere)

        
        console.log('finished sphere')
        console.log(scene)

        return scene
    }

    async parseCSV() {
        try {

            // 1. create url from the file
            const fileUrl = URL.createObjectURL(this.file);

            // 2. use fetch API to read the file
            const response = await fetch(fileUrl);

            // 3. get the text from the response
            const text = await response.text();

            // 4. split the text by newline
            const lines = text.split("\n");

            // 5. map through all the lines and split each line by comma.
            const data = lines.map((line) => line.split(","));

            return data

            } catch (error) {
                console.error(error);
            }
    }
}

export default Points