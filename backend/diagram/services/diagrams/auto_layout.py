import networkx as nx

from diagram.models import Diagram


def auto_layout_diagram(diagram: Diagram) -> Diagram:
    graph = nx.Graph()
    
    nodes = list(diagram.nodes.all())

    for node in nodes:
        graph.add_node(node.id)

    for edge in diagram.edges.all():
        graph.add_edge(edge.source.id, edge.target.id)

    if not nodes:
        return diagram

    positions = nx.spring_layout(graph, scale=500)

    for node in nodes:
        x, y = positions[node.id]
        node.x_position = round(float(x))
        node.y_position = round(float(y))
        
    diagram.nodes.bulk_update(
        nodes,
        ["x_position", "y_position"]
    )

    return diagram
