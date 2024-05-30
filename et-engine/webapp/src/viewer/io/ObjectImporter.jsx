import { fromBlob, fromArrayBuffer  } from "geotiff";

export default async function FetchObjectParameters(type, file) {

    let parameters = null
    let name = null
    switch (type) {
        case "Surface":
            parameters = await importSurface(file[0])
            name = file[0].name
            
            break;

        case "Lines":
            if (typeof file === 'string') {

                parameters = await importLines(file)
                name = 'New Lines'

            } else if (typeof file === 'object') {

                parameters = await importLines(await file[0].text())
                name = file[0].name

            }         
            break

        case "Volume":
            if (typeof file === 'string') {

                parameters = await importVolume(file)
                name = 'New Volume'

            } else if (typeof file === 'object') {

                parameters = await importVolume(await file[0].text())
                name = file[0].name
                
            }         
            break

        case "Ensemble":
            parameters = await importEnsemble(file)
            name = 'New Ensemble'
            break

        case "Drillhole":
            if (typeof file === 'string') {

                parameters = await importDrillhole(file)
                name = 'New Drillhole'

            } else if (typeof file === 'object') {

                parameters = await importDrillhole(await file[0].text())
                name = file[0].name
                
            }          
            break;

        default:
            console.log('Did not recognize case')
            break;
    }

    return [parameters, name]
}


async function importSurface(file) {
    // console.log(file)
    const tiff = await fromBlob(file)
    // const tiff = await fromArrayBuffer(file)
    const image = await tiff.getImage()
    const data = await image.readRasters({interleave: true});
    const origin = image.getOrigin()
    const resolution = image.getResolution()

    const parameters = {
        origin: origin,
        resolution: resolution,
        data: data,
        noData:-32767
    }

    return parameters
}

async function importLines(fileText) {

    // 4. split the text by newline
    const lines = fileText.split("\n");

    // 5. map through all the lines and split each line by comma.
    const data = lines.map((line) => line.split(","));

    // Push all the columns to the fields property
    const fields = []
    for (let i=0; i<data[0].length; i++) fields.push(data[0][i])

    const parameters = {
        xColumn: "x_27",
        yColumn: "y_27",
        zColumn: "altitude",
        lineColumn: "Line",
        points: data,
        fields: fields
    }

    return parameters

}

async function importEnsemble(files) {
    // This global parameter will be used in the loop
    const numRealizations = files.length

    // Holds all the meshes and geometries
    const realizationParameters = []
    const fileNames = []

    // Loop through all the files and load them as MultiVolume objects
    for (let i = 0; i < numRealizations; i++) {

        const parameters = await importVolume(await files[i].text())
        realizationParameters.push(parameters)
        fileNames.push(files[i].name)

    }

    const parameters = {
        realizationParameters: realizationParameters,
        fileNames: fileNames
    }

    return parameters
}


async function importVolume(fileText) {

    // 4. split the text by newline
    let lines = fileText.split("\n");

    // Pop the first number, which represents the number of vertices
    const numVertices = Number(lines.shift())

    // Pull the next numVertices lines since these represent the vertices
    const vertices = lines.slice(0, numVertices)

    // Update lines by getting rid of all the vertices
    lines = lines.slice(numVertices)

    // The next value after the vertices represents the number of voxels
    const numVoxels = Number(lines.shift())

    // Pull next numVoxels lines since these represent the voxels
    const voxels = lines.slice(0, numVoxels)

    // The remaining lines are the vertex values
    const values = lines.slice(numVoxels)

    // Loop through all the vertices
    for (let i = 0; i < numVertices; i++) {

        // Turn the coordinates & values into numbers
        vertices[i] = vertices[i].split(" ").map((v) => Number(v))
        values[i] = Number(values[i])
    }

    // Loop through all the voxels and turn them into numbers
    for (let i = 0; i < numVoxels; i++) {
        voxels[i] = voxels[i].split(" ").map((v) => Number(v))
    }
    const parameters = {
        vertices: vertices,
        voxels: voxels,
        values: values
    }
    
    return parameters
}

async function importDrillhole(fileText) {

    // 4. split the text by newline
    let lines = fileText.split("\n");

    // First row is the drillhole parameters
    const drillholeParams = lines.shift().split(" ").map((v) => Number(v))
    const collar = [drillholeParams[0], drillholeParams[1], drillholeParams[2]]
    const dip = drillholeParams[3]
    const dipDirection = drillholeParams[4]

    // Interval array
    const numIntervals = Number(lines.shift())//.map((v) => Number(v))
    const length = drillholeParams[5] * (numIntervals - 1)

    const intervals = []
    for (let i = 0; i < numIntervals; i++) {
        intervals.push(Number(lines.shift()))
    }

    // Observation arrays (e.g. borehole logs)
    const numObservations = Number(lines.shift())
    const observations = []
    for (let i = 0; i < numObservations; i++) {

        const currentObservation = []
        for (let j = 0; j < numIntervals; j++) {
            currentObservation.push(Number(lines.shift()))
        }

        observations.push(currentObservation)
    }
    
    const parameters = {
        numIntervals: numIntervals,
        numObservations: numObservations,
        intervals: intervals,
        observations: observations,
        collar: collar,
        dip: dip,
        dipDirection: dipDirection,
        length: length
    }
    return parameters

}