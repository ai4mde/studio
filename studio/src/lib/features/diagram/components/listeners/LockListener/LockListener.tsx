import { useDiagramStore } from "$diagram/stores";
import React, { useEffect } from "react";
import { useStoreApi } from "reactflow";

/**
 * This components listens for changes in the lock in the DiagramStore,
 * and sets React Flow's interactivity accordingly
 */
const LockListener: React.FC = () => {
    const { lock } = useDiagramStore();
    const store = useStoreApi();

    useEffect(() => {
        store.setState({
            nodesDraggable: !lock,
            nodesConnectable: !lock,
            elementsSelectable: !lock,
        });
    }, [lock]);

    return <></>;
};

export default LockListener;
