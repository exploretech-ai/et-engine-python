import getObject from "./ObjectKeys";

/**
 * Custom class that controls the checkbox properties in a way that is easily compatible with react states
 */
class LayerProps {

    /**
     * Constructs an empty and invisible set of checkbox properties
     * @param {string} id unique ID associated with the checkbox
     */
    constructor(id) {
      this.id = id                  // This property never changes
  
      this.visible = false          // This controls whether the checkbox is visible
      this.checked = false          // This controls whether the checkbox is checked
      this.label = id               // This is the label displayed next to the checkbox
      this.object = null            // This is the layer loaded from the file
  
      this.renaming = false         // This signals whether the render the renaming element
      this.styling = false          // This signals whether the render the styling element 
    }
  
    /**
     * Resets the properties to the initialized state, deleting any geometries and scenes and rendering the checkbox invisible
     */
    reset() {
      this.label = this.id 
  
      this.visible = false
      this.checked = false
      this.object = null
  
      this.renaming = false
      this.styling = false
    }
  
    /**
     * Copies the checkbox properties to a new object
     * @returns a new CheckboxProps with the same properties as the current object
     */
    clone() {
      const newCheckboxProps = new LayerProps(this.id)
  
      newCheckboxProps.label = this.label
  
      newCheckboxProps.visible = this.visible
      newCheckboxProps.checked = this.checked
      newCheckboxProps.object = this.object
  
      newCheckboxProps.renaming = this.renaming
      newCheckboxProps.styling = this.styling
  
      return newCheckboxProps
    }

    async set(parameters, objectType, label) {

      const newObject = new objectType(parameters)

      await newObject.initialize()
      newObject.setScene()

      this.visible = true
      this.checked = true
      this.label = label
      this.object = newObject
    }

    async toFile () {
      const fileContents = [
        'ID: ', this.id, '\n',
        'visible: ', String(this.visible), '\n',
        'checked: ', String(this.checked), '\n',
        'label: ', this.label, '\n',
        'object: '
      ]

      if (this.object) {
        fileContents.push(this.object.type, '\n')
        fileContents.push(JSON.stringify(this.object.parameters))
      } else {
        fileContents.push(null, '\n')
      }
      

      return fileContents.join('')
    }

    async setFromFile(fileContentsString) {

      const fileLines = fileContentsString.split('\n')

      const ID = fileLines.shift()
      const visible = fileLines.shift()
      const checked = fileLines.shift()
      const label = fileLines.shift()
      const objectTypeKey = fileLines.shift()
      const objectData = fileLines

      // >>>>>
      // THIS NEEDS TO BE UPDATED
      if (objectData[0] !== '') {
        const objectType = getObject(objectTypeKey.split(':')[1].trim())
        await this.set(JSON.parse(objectData), objectType, label.split(':')[1].trim())
      } 
      // =====

      // <<<<<
      
      this.visible = (visible.split(':')[1].trim() === "true")
      this.checked = (checked.split(':')[1].trim() === "true")

    }
    
  }
  
  export default LayerProps