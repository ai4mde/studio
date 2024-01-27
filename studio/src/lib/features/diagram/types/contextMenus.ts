import { Edge, Node } from 'reactflow'

export type PaneContextMenuState = {
    active: boolean
    x: number
    y: number
    open: (x: number, y: number) => void
    close: () => void
}

export type NodeContextMenuState = {
    active: boolean
    x: number
    y: number
    node?: Node
    open: (x: number, y: number, node: Node) => void
    close: () => void
}

export type EdgeContextMenuState = {
    active: boolean
    x: number
    y: number
    edge?: Edge
    open: (x: number, y: number, edge: Edge) => void
    close: () => void
}

export type SelectionContextMenuState = {
    active: boolean
    x: number
    y: number
    nodes?: Node[]
    edges?: Edge[]
    open: (x: number, y: number, nodes: Node[], edges: Edge[]) => void
    close: () => void
}
