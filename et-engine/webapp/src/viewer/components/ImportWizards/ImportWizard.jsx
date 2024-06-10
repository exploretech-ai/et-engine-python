import React from 'react'
import './modal.css'

import SurfaceModal from './SurfaceModal'
import LinesModal from './LinesModal'
import EnsembleModal from './EnsembleModal'
import DrillholeModal from './DrillholeModal'
import PointsModal from './PointsModal'

const ImportWizard = ({modalKey, toggleOpen}) => {

  function getModal(key) {
    switch(key) {
      case "Surface":
        return <SurfaceModal toggleOpen={toggleOpen}/>
      case "Lines":
        return <LinesModal toggleOpen={toggleOpen}/>
      case "Volume":
        return null
      case "Ensemble":
        return <EnsembleModal toggleOpen={toggleOpen}/>
      case "Drillhole":
        return <DrillholeModal toggleOpen={toggleOpen}/>
      case "Points":
        return <PointsModal toggleOpen={toggleOpen}/>
      default:
        console.log(`Object key ${key} not recognized`)
        return null
    }
}

  return (
    <div className="modal">
      <div className="modal-content">
        <span className="close" onClick={toggleOpen}>&times;</span>
        {getModal(modalKey)} 
      </div>
    </div>
  )
}


export default ImportWizard
