import React from "react";
import { useOnSelectionChange, useStoreApi } from "reactflow";
import { useDiagramStore } from "$diagram/stores/diagramState";

/**
 * This component exists solely to set the "nodeSelectionActive" to
 * true if nodes are selected using modifier & click, other than the
 * userSelect (box select / modifier & drag).
 *
 * To be fixed upstream.
 */
const SelectionListener: React.FC = () => {
    const store = useStoreApi();
    const { edges, setEdges } = useDiagramStore();

    // Listen to a new selection
    useOnSelectionChange({
        onChange: ({ nodes }) => {
            // Check if we have selected more than one node
            if (nodes.filter((e) => e.selected).length > 1) {
                // Don't continue if user is drag-selecting
                if (!store.getState().userSelectionActive) {
                    // Select only edges between clicked nodes
                    setEdges(
                        edges.map((e) => {
                            const sourceSelected = !!nodes.find(
                                (n) => n.id == e.source,
                            );
                            const targetSelected = !!nodes.find(
                                (n) => n.id == e.target,
                            );
                            return {
                                ...e,
                                selected: sourceSelected && targetSelected,
                            };
                        }),
                    );

                    // Let React Flow draw a rect between the selected nodes
                    store.setState({
                        nodesSelectionActive: true,
                    });
                }
            }
        },
    });

    return <></>;
};

export default SelectionListener;
