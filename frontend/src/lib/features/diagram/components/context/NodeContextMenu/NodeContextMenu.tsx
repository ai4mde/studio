import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";
import { startManualConnect } from "$diagram/events";
import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useNodeContextMenu } from "$diagram/stores/contextMenus";
import { useEditNodeModal } from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Copy, Edit, GitBranchPlus, Trash, UploadCloud, PlusCircle } from "lucide-react";
import React, { MouseEventHandler, useState, useRef } from "react";
import { useStoreApi } from "reactflow";

const NodeContextMenu: React.FC = () => {
    const { x, y, node, close } = useNodeContextMenu();
    const { diagram, nodes } = useDiagramStore();
    const editNode = useEditNodeModal();
    const { setState, getState } = useStoreApi();

    const swimlaneButtonRef = useRef<HTMLLIElement>(null);
    const [showSwimlanes, setShowSwimlanes] = useState(false);
    const swimlaneGroup = nodes.filter((n) => n.data.type === 'swimlanegroup')[0];

    const onEdit = () => {
        node && editNode.open(node.id);
        close();
    };

    const onDelete = async () => {
        if (node) {
            await authAxios.delete(`/v1/diagram/${diagram}/node/${node.id}/`);

            await queryClient.refetchQueries({
                queryKey: [`diagram`],
            });
        }
        close();
    };

    const onConnect: MouseEventHandler<HTMLButtonElement> = (e) => {
        node && startManualConnect(e, node, getState, setState);
        close();
    };

    const handleMouseEnter = () => {
        setShowSwimlanes(true);
    }

    const handleMouseLeave = () => {
        setShowSwimlanes(false);
    }

    const addToSwimlane = (nodeId: string, actorNodeId: string) => {
        console.log(nodeId, actorNodeId);
        partialUpdateNode(diagram, nodeId, {
            cls: {
                actorNode: actorNodeId,
            }
        });
        queryClient.refetchQueries({
            queryKey: [`diagram`],
        });
        close();
    }

    return (
        <>
            <ContextMenu x={x} y={y}>
                <>
                    <li>
                        <button onClick={onEdit}>
                            <span>Edit</span>
                            <Edit size={14} />
                        </button>
                    </li>
                    <hr className="my-1" />
                    {node.data.type !== 'swimlanegroup' && (
                        <li>
                            <button onClick={onDelete}>
                                <span>Delete</span>
                                <Trash size={14} />
                            </button>
                        </li>
                    )}
                    <li>
                        <button disabled>
                            <span>Copy</span>
                            <Copy size={14} />
                        </button>
                    </li>
                    <hr className="my-1" />
                    <li>
                        <button onClick={onConnect}>
                            <span>Connect</span>
                            <GitBranchPlus size={14} />
                        </button>
                    </li>
                    {['action', 'control', 'object'].includes(node.data.type) && (
                         <li
                         ref={swimlaneButtonRef}
                         onMouseEnter={handleMouseEnter}
                         onMouseLeave={handleMouseLeave}
                         style={{ position: 'relative' }}
                     >
                         <button>
                             <span>Add to swimlane</span>
                             <PlusCircle size={14} />
                         </button>
                         {showSwimlanes && swimlaneButtonRef.current && (
                             <ContextMenu
                                 x={swimlaneButtonRef.current.getBoundingClientRect().right}
                                 y={swimlaneButtonRef.current.getBoundingClientRect().top}
                             >
                                 <>
                                    {swimlaneGroup?.data.swimlanes.map((swimlane, index) => (
                                        <li key={index}>
                                            <button
                                                onClick={() => addToSwimlane(node.id, swimlane.actorNode)}
                                                className={node?.data.actorNode === swimlane.actorNode ? 'bg-blue-600 text-gray-50' : ''}
                                            >
                                                <span>{swimlane.actorNodeName}</span>
                                            </button>
                                        </li>
                                    ))}
                                 </>
                             </ContextMenu>
                         )}
                     </li>
                    )}
                    <hr className="my-1" />
                    <li>
                        <button>
                            <span>Upload as Component</span>
                            <UploadCloud size={14} />
                        </button>
                    </li>
                </>
            </ContextMenu>
        </>
    );
};

export default NodeContextMenu;
