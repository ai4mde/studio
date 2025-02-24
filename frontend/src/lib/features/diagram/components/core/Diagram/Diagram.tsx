import {
    onEdgeContextMenu,
    onMove,
    onNodeClick,
    onNodeContextMenu,
    onPaneClick,
    onPaneContextMenu,
    onSelectionContextMenu,
} from "$diagram/events";
import { navigationPortalAtom } from "$shared/hooks/navigationPortal";
import { useAtom } from "jotai";
import React, { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Background, ControlButton, Controls, ReactFlow } from "reactflow";
import "reactflow/dist/style.css";

import { useDiagram } from "$diagram/queries";
import { useDiagramStore } from "$diagram/stores";

import { ContextMenus } from "$diagram/components/context";
import { DiagramControls } from "$diagram/components/toolbar";

import { nodeTypes } from "$diagram/components/core/Node/Node";
import {
    FloatingConnectionLine,
    Markers,
    edgeTypes,
} from "$diagram/components/edges";
import { Listeners } from "$diagram/components/listeners";
import { Modals } from "$diagram/components/modals";
import { CommandMenu } from "$diagram/components/prompt";
import { Screens } from "$diagram/components/screens";
import {
    useEditConnectionModal,
    useEditNodeModal,
    useNewConnectionModal,
} from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import { LinearProgress } from "@mui/joy";
import { toSvg } from 'html-to-image';
import { Download, Move3d } from 'lucide-react';


const multiSelectionKeyCodes = ["Meta", "Shift"];

type Props = {
    diagram: string;
};

const Diagram: React.FC<Props> = ({ diagram }) => {
    const diagramStore = useDiagramStore();
    const [navRef] = useAtom(navigationPortalAtom);
    const { data, isSuccess, dataUpdatedAt } = useDiagram(diagram);
    const editNodeModal = useEditNodeModal();
    const newConnectionModal = useNewConnectionModal();
    const editConnectionModal = useEditConnectionModal();
    const flowRef = useRef<HTMLDivElement>(null);

    // On load, push the diagram URL to the diagram store as well
    useEffect(() => {
        diagramStore.setDiagramID(diagram);

        if (isSuccess) {
            diagramStore.setType(data.type);
            diagramStore.setProject(data.project);
            diagramStore.setSystem(data.system);
        }
    }, [isSuccess]);

    // If our data changes, force-update the state of the nodes or edges
    useEffect(
        () => diagramStore.nodesFromAPI(data?.nodes ?? []),
        [dataUpdatedAt],
    );
    useEffect(
        () => diagramStore.edgesFromAPI(data?.edges ?? []),
        [dataUpdatedAt],
    );

    if (!isSuccess) {
        return <LinearProgress className="absolute top-0 left-0 right-0" />;
    }

    return (
        <div
            style={{ height: "100%" }}
            ref={flowRef}
        >
            <Markers />
            <ReactFlow
                nodes={diagramStore.nodes}
                onNodesChange={
                    diagramStore.lock ? diagramStore.onNodesChange : undefined
                }
                edges={diagramStore.edges}
                edgeTypes={edgeTypes}
                onEdgesChange={
                    diagramStore.lock ? diagramStore.onEdgesChange : undefined
                }
                nodeTypes={nodeTypes}
                onPaneContextMenu={onPaneContextMenu}
                onPaneClick={onPaneClick}
                elementsSelectable
                onMove={onMove}
                onNodeClick={onNodeClick}
                onNodeDoubleClick={(_, node) => {
                    editNodeModal.open(node.id);
                }}
                onNodeContextMenu={onNodeContextMenu}
                onEdgeDoubleClick={(_, edge) => {
                    editConnectionModal.open(edge.id);
                }}
                onEdgeContextMenu={onEdgeContextMenu}
                onSelectionContextMenu={onSelectionContextMenu}
                onConnectStart={() => diagramStore.setConnecting(true)}
                onConnectEnd={() => diagramStore.setConnecting(false)}
                autoPanOnConnect
                onConnect={(e) =>
                    e.source &&
                    e.target &&
                    newConnectionModal.open(e.source, e.target)
                }
                connectionLineComponent={FloatingConnectionLine}
                multiSelectionKeyCode={multiSelectionKeyCodes}
                snapToGrid
                fitView
            >
                <Background />
                <Controls showInteractive={false} >
                    <ControlButton title="auto layout" onClick={async () => {
                        await authAxios.post(`/v1/diagram/${diagram}/auto_layout`);
                        const updatedDiagram = await authAxios.get(`/v1/diagram/${diagram}`);
                        diagramStore.nodesFromAPI(updatedDiagram.data?.nodes ?? []);
                        diagramStore.edgesFromAPI(updatedDiagram.data?.edges ?? []);
                    }}>
                        <Move3d />
                    </ControlButton>
                    <ControlButton title="download svg" onClick={() => {
                        if (flowRef.current === null) return;
                        toSvg(flowRef.current, {
                            filter: node => !(
                                node?.classList?.contains('react-flow__minimap') ||
                                node?.classList?.contains('react-flow__controls') ||
                                node?.classList?.contains('react-flow__background')
                            ),
                        }).then(dataUrl => {
                            const a = document.createElement('a');
                            a.setAttribute('download', diagram + '.svg');
                            a.setAttribute('href', dataUrl);
                            a.click();
                        });
                    }}>
                        <Download />
                    </ControlButton>
                </Controls>
                <ContextMenus />
                <Modals />
                <Screens />
                <Listeners />

                {createPortal(<CommandMenu />, document.body)}

                {navRef.current &&
                    createPortal(<DiagramControls />, navRef.current)}

            </ReactFlow>
        </div>
    );
};

export default Diagram;
