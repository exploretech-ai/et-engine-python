import Surface from "../layers/Surface"
import Lines from "../layers/Lines"
import Ensemble from "../layers/Ensemble"
import Volume from "../layers/Volume"
import Drillhole from "../layers/Drillhole"

export default function getObject(key) {

    switch(key) {
        case "Surface":
            return Surface
        case "Lines":
            return Lines
        case "Volume":
            return Volume
        case "Ensemble":
            return Ensemble
        case "Drillhole":
            return Drillhole
        default:
            console.log(`Object key ${key} not recognized`)
    }
}