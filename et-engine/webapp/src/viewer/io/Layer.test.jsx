import Layer from "../objects/Layer";
import LayerProps from "./Layer";
import FetchObjectParameters from "./ObjectImporter";
import getObject from "./ObjectKeys";

test('layer clones properly', () => {
    const originalLayer = new LayerProps(0)
    const clonedLayer = originalLayer.clone()

    expect(clonedLayer).toEqual(originalLayer)      // Properties identical
    expect(clonedLayer).not.toBe(originalLayer)     // Not at the same memory address

}) 


test('empty layer is the same after saving and loading', async () => {
    const originalLayer = new LayerProps(0)
    const properties = await originalLayer.toFile()
    
    const newLayer = originalLayer.clone()
    await newLayer.setFromFile(properties)

    expect(newLayer).toEqual(originalLayer)      // Properties identical
    expect(newLayer).not.toBe(originalLayer)     // Not at the same memory address

}) 


test.each([
    ['../../test/lines.csv', 'Lines'],
    ['../../test/volume0.mesh', 'Volume'],
    ['../../test/drillhole.dh', 'Drillhole'],
])('loading %s as %s', async (relativePath, ObjectKey) => {
    const fs = require("fs");
    const path = require("path");

    const originalLayer = new LayerProps(0)
    const fullPath = path.join(__dirname, relativePath);

    const file = fs.readFileSync(fullPath)

    const [parameters, name] = await FetchObjectParameters(ObjectKey, file.toString())
    const ObjectType = getObject(ObjectKey)
    originalLayer.set(parameters, ObjectType, name)

    const clonedLayer = originalLayer.clone()

    expect(clonedLayer).toEqual(originalLayer)      // Properties identical
    expect(clonedLayer).not.toBe(originalLayer)     // Not at the same memory address

    // const properties = await originalLayer.toFile()
    // const newLayer = new LayerProps(0)
    // await newLayer.setFromFile(properties)

    // expect(newLayer).toEqual(originalLayer)      // Properties identical
    // expect(newLayer).not.toBe(originalLayer)     // Not at the same memory address


})


// test('loading surface', async () => {
//     const relativePath = '../../test/surface.tif'
//     const ObjectKey = 'Surface'

//     const fs = require("fs");
//     const path = require("path");
//     const { Blob } = require("buffer")

//     const originalLayer = new LayerProps(0)
//     const fullPath = path.join(__dirname, relativePath);

//     let buffer = fs.readFileSync(fullPath)
//     let file = buffer.buffer
    
//     const [parameters, name] = await FetchObjectParameters(ObjectKey, [file])
//     const ObjectType = getObject(ObjectKey)
//     originalLayer.set(parameters, ObjectType, name)

// })

// test('loading ensemble', () => {
//     const filePaths = ['../../test/volume0.mesh', '../../test/volume1.mesh', '../../test/volume2.mesh']
// })

