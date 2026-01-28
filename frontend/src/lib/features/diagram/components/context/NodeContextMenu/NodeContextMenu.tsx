import ContextMenu from "$diagram/components/context/ContextMenu/ContextMenu";
import { startManualConnect } from "$diagram/events";
import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useNodeContextMenu } from "$diagram/stores/contextMenus";
import { useEditNodeModal, useConfirmDeleteClassifierModal } from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Copy, Edit, GitBranchPlus, Trash, UploadCloud, PlusCircle, MinusCircle } from "lucide-react";
import React, { MouseEventHandler, useState, useRef, useEffect } from "react";
import { useStoreApi } from "reactflow";
import DeleteConfirmationModal from "$diagram/components/modals/DeleteConfirmationModal/DeleteConfirmationModal";

const NodeContextMenu: React.FC = () => {
    const { x, y, node, close } = useNodeContextMenu();
    const { diagram, nodes, relatedDiagrams } = useDiagramStore();
    const { setState, getState } = useStoreApi();
    
    const [canRemove, setCanRemove] = useState(true);
    const [checkingUsage, setCheckingUsage] = useState(false);

    const confirmDeleteClassifierModal = useConfirmDeleteClassifierModal();
    const editNode = useEditNodeModal();

    const swimlaneButtonRef = useRef<HTMLLIElement>(null);
    const [showSwimlanes, setShowSwimlanes] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const swimlaneGroup = nodes.filter((n) => n.data.type === 'swimlanegroup')[0];
    const systemBoundary = nodes.filter((n) => n.data.type === 'system_boundary')[0];

    useEffect(() => {
            let cancelled = false;
    
            const run = async () => {
                if (!node) return;
                setCheckingUsage(true);
    
                try {
                    const res = await authAxios.get(`/v1/diagram/${diagram}/node/${node.id}/classifier-usage/`,);
                    const usages = res.data?.usages ?? [];
                    const allowRemove = usages.length > 0;
                    if (!cancelled) setCanRemove(allowRemove);
                } catch {
                    if (!cancelled) setCanRemove(true);
                } finally {
                    if (!cancelled) setCheckingUsage(false);
                }
            };
    
            run();
            return () => {
                cancelled = true;
            };
        }, [node?.id, diagram]);
    

    const onEdit = () => {
        node && editNode.open(node.id);
        close();
    };

    const onRemove = async () => {
        if (node) {
            await authAxios.delete(`/v1/diagram/${diagram}/node/${node.id}/`);
            await queryClient.refetchQueries({
                queryKey: [`diagram`],
            });
            close();
        }
    };

    const onDeleteCompletely = async () => {
        if (node) {
            const res = await authAxios.get(`/v1/diagram/${diagram}/node/${node.id}/classifier-usage/`);
            confirmDeleteClassifierModal.open({
                nodeId: node.id,
                classifierName: res.data.classifier_name,
                usages: res.data.usages,
            });

            close();
        }
    };

    const onDelete = async (force: boolean = false) => {
        if (!node) {
            close();
            return;
        }

        // If an actor is deleted, we need to check if it is associated with any action nodes
        if (node.data.type === 'actor' && !force) {
            const relatedActionNodes = relatedDiagrams
                .filter((d) => d.type === 'activity')
                .flatMap((d) => d.nodes)
                .filter((n) => n?.actorNode === node.id);
            if (relatedActionNodes.length > 0) {
                setShowDeleteModal(true);
                return;
            }
        }
        await authAxios.delete(`/v1/diagram/${diagram}/node/${node.id}/`);
        await queryClient.refetchQueries({
            queryKey: [`diagram`],
        });
        close();
    };

    const confirmDelete = async (confirm: boolean) => {
        await onDelete(true);
        setShowDeleteModal(false);
        close();
    }

    const cancelDelete = () => {
        setShowDeleteModal(false);
    }


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

    const updateParenting = (
      nodeId: string,
      opts: {
        remove: boolean;
        parentId: string | null;
        clsPatch: Record<string, any>;
      }
    ) => {
      const currentNode = nodes.find((n) => n.id === nodeId)
      if (!currentNode) return;

      let newPosition = currentNode.position;

      if (opts.parentId) {
        const parentNode = nodes.find((n) => n.id === opts.parentId);
        if (parentNode) {
          newPosition = opts.remove
            ? {
                x: currentNode.position.x + parentNode.position.x,
                y: currentNode.position.y + parentNode.position.y,
              }
            : {
                x: currentNode.position.x - parentNode.position.x,
                y: currentNode.position.y - parentNode.position.y,
              };
        }
      }

      partialUpdateNode(diagram, nodeId, {
        cls: opts.clsPatch,
        data: {
          position: newPosition,
        },
      });
      queryClient.refetchQueries({
        queryKey: [`diagram`],
      });
      close();
    }

    const addToSwimlane = (nodeId: string, actorNodeId: string) => {
      const currentNode = nodes.find((n) => n.id === nodeId);
      const remove = currentNode?.data.actorNode === actorNodeId;

      updateParenting(nodeId, {
        remove,
        parentId: swimlaneGroup?.id ?? null, // or swimlaneGroupUUID if that's your parent id
        clsPatch: { actorNode: remove ? null : actorNodeId },
      });
    };

    const addToParentNode = (nodeId: string, remove: boolean, parentNodeId: string) => {
      updateParenting(nodeId, {
        remove,
        parentId: parentNodeId,
        clsPatch: { parentNode: remove ? null : parentNodeId },
      });
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
                        <button
                            onClick={onRemove}
                            disabled={!canRemove || checkingUsage}
                        >
                            <span>Remove from Diagram</span>
                            <Trash size={14} />
                        </button>
                    </li>
                    <li>
                        <button onClick={onDeleteCompletely}>
                            <span>Delete Completely</span>
                            <Trash size={14} />
                        </button>
                    </li>
                    {node.data.type !== 'swimlanegroup' && (
                        <li>
                            <button onClick={() => onDelete()}>
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
                             <MinusCircle size={14} />
                         </button>
                         {showSwimlanes && swimlaneButtonRef.current && (
                             <ContextMenu
                                 x={swimlaneButtonRef.current.getBoundingClientRect().right}
                                 y={swimlaneButtonRef.current.getBoundingClientRect().top}
                             >
                                 <>
                                    {swimlaneGroup?.data.swimlanes
                                        .filter((swimlane) => swimlane.actorNodeName !== 'Unknown actor')
                                        .map((swimlane, index) => (
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
                    {['usecase', 'actor'].includes(node.data.type) && systemBoundary && (
                      <li>
                        <button onClick={() => addToParentNode(
                              node.id,
                              node.data?.parentNode ? true: false,
                              systemBoundary ? systemBoundary.id : ''
                            )}
                          >
                            <span>
                              {node.data?.parentNode ? 'Remove from System' : 'Add to System'}
                            </span>
                            {node.data?.parentNode ? <MinusCircle size={14} /> : <PlusCircle size={14} />}
                        </button>
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
            {showDeleteModal && (
                <DeleteConfirmationModal
                    text="This actor is associated with a one or more action nodes. Deleting this actor will delete this association. Do you wish to continue?"
                    showNoButton={false}
                    onConfirm={confirmDelete}
                    onCancel={cancelDelete}
                />
            )}
        </>
    );
};

export default NodeContextMenu;
