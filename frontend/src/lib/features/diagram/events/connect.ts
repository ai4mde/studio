import { MouseEvent as ReactMouseEvent } from "react";
import { Node, ReactFlowState } from "reactflow";

export const startManualConnect = (
    e: ReactMouseEvent<HTMLButtonElement>,
    node: Node,
    getState: () => ReactFlowState,
    setState: (state: Partial<ReactFlowState>) => void,
) => {
    const { domNode, onConnectEnd, onConnectStart } = getState();
    const doc =
        ((e.target as HTMLElement)?.getRootNode?.() as Document | ShadowRoot) ??
        window?.document;

    const bounds = domNode?.getBoundingClientRect();

    const followConnect = (e: MouseEvent) => {
        setState({
            connectionPosition: {
                x: e.clientX - (bounds?.left ?? 0),
                y: e.clientY - (bounds?.top ?? 0),
            },
        });
    };

    const tryConnect = (e: MouseEvent) => {
        e.preventDefault();

        const { onConnectEnd, onConnect } = getState();

        const element = doc
            .elementsFromPoint(e.clientX, e.clientY)
            .filter((el) => el.classList.contains("react-flow__handle"))
            .find((el) => el.classList.contains("target"));

        if (element) {
            const nodeId = element.getAttribute("data-nodeid");

            if (nodeId && node?.id && nodeId != node.id) {
                console.log(`should connect ${node.id} to ${nodeId}`);
                onConnect?.({
                    source: node.id,
                    target: nodeId,
                    sourceHandle: "glob",
                    targetHandle: "glob",
                });
            }
        }

        // Drop Connection
        setState({
            connectionPosition: undefined,
            connectionNodeId: null,
            connectionHandleId: null,
            connectionHandleType: null,
            connectionStartHandle: null,
        });

        // Run End Connection
        onConnectEnd?.(e);
        return;
    };

    node &&
        setState({
            connectionPosition: {
                x: e.clientX - (bounds?.left ?? 0),
                y: e.clientY - (bounds?.top ?? 0),
            },
            connectionNodeId: node.id,
            connectionHandleId: `glob`,
            connectionHandleType: "source",
            connectionStartHandle: {
                nodeId: node.id,
                handleId: `glob`,
                type: "source",
            },
            onConnectEnd: (e) => {
                onConnectEnd && onConnectEnd(e);
                domNode?.removeEventListener("mousemove", followConnect);
                domNode?.removeEventListener("click", tryConnect);
                setState({
                    onConnectEnd,
                });
            },
        });

    domNode?.addEventListener("mousemove", followConnect);
    domNode?.addEventListener("click", tryConnect, { once: true });

    onConnectStart &&
        onConnectStart(e as any, {
            nodeId: node?.id ?? null,
            handleId: "glob",
            handleType: "source",
        });
};
