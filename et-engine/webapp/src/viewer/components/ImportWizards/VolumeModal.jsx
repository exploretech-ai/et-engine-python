
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

export {importVolume}