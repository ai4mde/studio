import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";
import { startManualConnect } from "$diagram/events";
import { useDiagramStore } from "$diagram/stores";
import { useNodeContextMenu } from "$diagram/stores/contextMenus";
import { useEditNodeModal } from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Copy, Edit, GitBranchPlus, Trash, UploadCloud, PlusCircle } from "lucide-react";
import React, { MouseEventHandler, useState, useRef } from "react";
import { useStoreApi, Node } from "reactflow";
import { partialUpdateNode } from "$diagram/mutations/diagram";
import styles from './nodecontextmenu.module.css';
import DeleteConfirmationModal from "$diagram/components/modals/DeleteConfirmationModal/DeleteConfirmationModal";

const NodeContextMenu: React.FC = () => {
    const { x, y, node, close } = useNodeContextMenu();
    const { diagram, nodes } = useDiagramStore();
    const editNode = useEditNodeModal();
    const { setState, getState } = useStoreApi();

    const swimLanes = nodes.filter((n) => n.type === "swimlane");
    const swimlaneButtonRef = useRef<HTMLLIElement>(null);
    const [showSwimlanes, setShowSwimlanes] = useState(false);

    const [showPopup, setShowPopup] = useState(false);

    const onEdit = () => {
        node && editNode.open(node.id);
        close();
    };

    const onDelete = async (deleteChildNodes: boolean) => {
        if (node) {
            await authAxios.delete(`/v1/diagram/${diagram}/node/${node.id}/`, {
                params: { deleteChildNodes },
            });
            await queryClient.refetchQueries({
                queryKey: [`diagram`],
            });
            close();
        }
    };

    const onConnect: MouseEventHandler<HTMLButtonElement> = (e) => {
        node && startManualConnect(e, node, getState, setState);
        close();
    };

    const onSwimlaneAdd = (swimLane: Node) => {
        if (node) {
            // set parent node of action node to swimlane
            // calculate new position of action node relative to swimlane
            // set position of action node relative to swim
            partialUpdateNode(diagram, node.id, {
                cls: {
                    parentNode: swimLane.id,
                }
            })
            queryClient.refetchQueries({
                queryKey: [`diagram`],
            });
        }
    }
    
    const handleMouseEnter = () => {
        setShowSwimlanes(true);
    };

    const handleMouseLeave = () => {
        setShowSwimlanes(false);
    };

    const handleDeleteClick = () => {
        if (node?.type === 'swimlane') {
            setShowPopup(true);
        } else {
            onDelete(false);
        }
        
    };

    const handleConfirmDelete = (deleteChildren: boolean) => {
        onDelete(deleteChildren);
        setShowPopup(false);
    };

    const handleCancelDelete = () => {
        setShowPopup(false);
    };

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
                    <li>
                        <button onClick={handleDeleteClick}>
                            <span>Delete</span>
                            <Trash size={14} />
                        </button>
                    </li>
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
                    {node?.type !== "swimlane" && (
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
                                        {swimLanes.map((swimLane) => (
                                            <li key={swimLane.id}>
                                                <button
                                                    onClick={() => onSwimlaneAdd(swimLane)}
                                                    className={node?.parentNode === swimLane.id ? styles.activeButton : ''}
                                                >
                                                    <span>{swimLane.data?.name}</span>
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

            {showPopup && (
                <DeleteConfirmationModal
                    onConfirm={handleConfirmDelete}
                    onCancel={handleCancelDelete}
                />
            )}
        </>
    );
};

export default NodeContextMenu;
