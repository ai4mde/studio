import { EdgeTypes } from 'reactflow'
import FloatingConnectionLine from './FloatingConnectionLine/FloatingConnectionLine'
import FloatingEdge from './FloatingEdge/FloatingEdge'
import Markers from './Markers/Markers'

const edgeTypes: EdgeTypes = {
    floating: FloatingEdge,
}

export { FloatingConnectionLine, FloatingEdge, Markers, edgeTypes }
export default { FloatingConnectionLine, FloatingEdge, Markers, edgeTypes }
