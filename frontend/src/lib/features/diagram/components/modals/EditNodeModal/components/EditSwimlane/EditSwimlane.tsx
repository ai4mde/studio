import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import React, { useState } from "react";
import { Node } from "reactflow";
import { Select, Option, Button } from "@mui/joy";
import { TrashIcon } from "lucide-react";
import DeleteConfirmationModal from "$diagram/components/modals/DeleteConfirmationModal/DeleteConfirmationModal";
import { authAxios } from "$auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import styles from './editswimlane.module.css';

type Props = {
    node: Node;
}

export const EditSwimlane: React.FC<Props> = ({ node }) => {
    const [value, setValue] = useState(node.data.swimlanes);
    const { diagram, nodes } = useDiagramStore();
    const [selectedSwimlaneUUID, setSelectedSwimlaneUUID] = useState(null);
    const [showPopup, setShowPopup] = useState(false);
    const swimlaneGroup = nodes.filter((n) => n.data?.type === 'swimlanegroup')[0];

    const deleteSwimlane = () => {
        const nodesToUpdate = nodes.filter((node) => node.data?.actorNode === selectedSwimlaneUUID);
        if (nodesToUpdate.length > 0) {
            setShowPopup(true);
        } else {
            handleConfirmDelete(false);
        }
    };

    const handleConfirmDelete = async (deleteChildren: boolean) => {
        const nodesToUpdate = nodes.filter((node) => node.data?.actorNode === selectedSwimlaneUUID);
        // If this is the last swimlane, delete the entire group
        if (value.length === 1) {
            console.log('delete swimlane group');
            await authAxios.delete(`/v1/diagram/${diagram}/node/${swimlaneGroup.id}/`);
        } else {
            partialUpdateNode(diagram, node.id, {
                cls: {
                    swimlanes: value.filter((swimlane) => swimlane.actorNode !== selectedSwimlaneUUID),
                }
            });
        }
        
        if (deleteChildren) {
            // Remove all nodes that have the swimlane as a parent
            nodesToUpdate.forEach(async (node) => {
                await authAxios.delete(`/v1/diagram/${diagram}/node/${node.id}/`);
            })
        } else {
            // Remove the swimlane as a parent from all nodes
            nodesToUpdate.forEach((node) => {
                partialUpdateNode(diagram, node.id, {
                    cls: {
                        actorNode: null,
                    }
                })
            })
        }

        // Close modal, reset state
        setShowPopup(false);
        setValue(value.filter((swimlane) => swimlane.actorNode !== selectedSwimlaneUUID));
        setSelectedSwimlaneUUID(null);

        await queryClient.refetchQueries({
            queryKey: ['diagram'],
        });
        close();
    }

    const onDragStart = (event, index) => {
        event.dataTransfer.setData("swimlaneIndex", index);
    };

    const onDragOver = (event) => {
        event.preventDefault();
    };

    const onDrop = (event, index) => {
        const draggedIndex = event.dataTransfer.getData("swimlaneIndex");
        const reorderedSwimlanes = Array.from(value);
        const [removed] = reorderedSwimlanes.splice(draggedIndex, 1);
        reorderedSwimlanes.splice(index, 0, removed);

        setValue(reorderedSwimlanes);

        partialUpdateNode(diagram, node.id, {
            cls: {
                swimlanes: reorderedSwimlanes,
            }
        });
    };

    return (
        <>
            <div className={styles.swimlaneOrder}>
                <span className={styles.swimlaneOrderTitle}>
                    Swimlane Order
                </span>
                <div>
                    {value.map((swimlane, index) => (
                        <div
                            key={swimlane.actorNode}
                            draggable
                            onDragStart={(event) => onDragStart(event, index)}
                            onDragOver={onDragOver}
                            onDrop={(event) => onDrop(event, index)}
                            className={styles.swimlaneItem}
                        >
                            <span>{swimlane.actorNodeName}</span>
                        </div>
                    ))}
                </div>
            </div>
            <div className="flex w-full flex-col gap-2 font-mono">
                <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                    Select Swimlane
                </span>
                <Select
                    value={selectedSwimlaneUUID}
                    onChange={(_, newValue) => setSelectedSwimlaneUUID(newValue)}
                    placeholder="Select Swimlane..."
                >
                    {node.data.swimlanes.map((swimlane) => (
                        <Option key={swimlane.actorNode} value={swimlane.actorNode}>
                            {swimlane.actorNodeName}
                        </Option>
                    ))}
                </Select>
            </div>
            {selectedSwimlaneUUID && (
                <>
                    <div className="flex w-full flex-col gap-2 font-mono">
                        <span className='w-full border-b border-solid border-gray-400 py-1 font-mono text-xs'>
                            Delete Swimlane
                        </span>
                        <div className="flex justify-start">
                            <Button
                                type='button'
                                color='danger'
                                onClick={deleteSwimlane}
                                className="w-auto"
                            >
                                <TrashIcon />
                            </Button>
                        </div>
                    </div>
                </>
            )}
            {showPopup && (
                <DeleteConfirmationModal
                    onConfirm={handleConfirmDelete}
                    onCancel={() => setShowPopup(false)}
                />
            )}
        </>
    )
}

export default EditSwimlane;