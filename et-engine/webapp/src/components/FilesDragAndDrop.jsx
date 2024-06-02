/*
https://betterprogramming.pub/how-to-implement-files-drag-and-drop-in-react-22cf42b7a7ef
*/
import React from 'react';
// import PropTypes from 'prop-types';

import './FilesDragAndDrop.css';



function FilesDragAndDrop({activeVFS, idToken, children}) {

    const onUpload = (files) => {

        console.log('Uploading files: ', files)
        Array.from(files).forEach(file => {
          fetch(
              "https://t2pfsy11r1.execute-api.us-east-2.amazonaws.com/prod/vfs/" + activeVFS.id, {
                  method: "POST",
                  headers: {
                      "Authorization": "Bearer " + idToken
                  },
                  body: JSON.stringify({key: file.name})
          }).then(response => {
              if (response.ok) {
                console.log('upload request sent')
                  return response.json()
              } else {
                  return "ERROR"
              }
          }).then(presignedUrl => {

              let data = new FormData()
              Object.keys(presignedUrl.fields).forEach(key => data.append(key, presignedUrl.fields[key]))
              data.append('file', file)

              console.log(presignedUrl)

              fetch(presignedUrl.url, {
                  method: 'POST',
                  body: data
              })
              .then(response => {
                if (response.ok) {
                  return response
                } else {
                  throw new Error('something went wrong')
                }
              })
              .then(response => {
                console.log('upload successful')
              })
              .catch(error => {
                console.error(error)
              })
            })  
            .catch(error => console.error(error))
        })
    }

  const drop = React.useRef(null)
  const drag = React.useRef(null)
  const [dragging, setDragging] = React.useState(false)

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }
  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragging(false)

    const {files} = e.dataTransfer
    if (files && files.length) { 
        console.log('Uploading files: ', files)
        onUpload(files)
    }
  }
  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()

    if (e.target !== drag.current) {
        setDragging(true)
    }
  }
  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()

    if (e.target === drag.current) {
        setDragging(false)
    }
  }

  React.useEffect(() => {

    const instance = drop.current;

    if (instance) {
      instance.addEventListener('dragover', handleDragOver)
      instance.addEventListener('drop', handleDrop)
      instance.addEventListener('dragenter', handleDragEnter)
      instance.addEventListener('dragleave', handleDragLeave)        
    }
    return () => {
      instance.removeEventListener('dragover', handleDragOver)
      instance.removeEventListener('drop', handleDrop)
      instance.removeEventListener('dragenter', handleDragEnter)
      instance.removeEventListener('dragleave', handleDragLeave)
    }
  }, [])

  return (
    <div ref={drop} className='overlayContainer'>
        {dragging && (
            <div ref={drag} className='overlay'>
            Drop here to upload file
            <span
              role='img'
              aria-label='emoji'
              className='area__icon'
            >
              &#128526;
            </span>
          </div>
        )}
      {children}
    </div>
  );
}

// FilesDragAndDrop.propTypes = {
//   onUpload: PropTypes.func.isRequired,
// };

export default FilesDragAndDrop