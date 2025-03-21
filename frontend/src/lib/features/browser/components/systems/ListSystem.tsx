import { useAtom } from "jotai";
import { Plus, X } from "lucide-react";
import { Button, Modal, ModalDialog, ModalClose, Divider } from '@mui/joy';
import React, { useState } from "react";
import { createSystemAtom } from "../../atoms";
import { useSystems } from "$browser/queries";
import { authAxios } from "$lib/features/auth/state/auth";

type Props = {
    project: string;
};

export const ListSystem: React.FC<Props> = ({ project }) => {
    const [, setCreate] = useAtom(createSystemAtom);
    const { data, isSuccess, refetch } = useSystems(project);
    const [showDeleteSystemModal, setShowDeleteSystemModal] = useState(false);
    const [systemToDelete, setSystemToDelete] = useState("");

    const handleDeleteSystem = async (systemId: string) => {
        try {
            await authAxios.delete(`/v1/metadata/systems/${systemId}/`);
        } catch (error) {
            console.error('Error deleting system:', error);
        } finally {
            setSystemToDelete("");
            setShowDeleteSystemModal(false);
            refetch();
        }
    }

    const openDeleteSystemModal = (systemId: string) => {
        setShowDeleteSystemModal(true);
        setSystemToDelete(systemId);
    }

    return (
        <>
            {isSuccess &&
                data.map((e) => (
                    <div key={e.id} className="relative w-48">
                        <a
                            href={`/systems/${e.id}`}
                            className="flex h-fit flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                        >
                            <h3 className="text-xl font-bold">{e.name}</h3>
                            <h3 className="text-sm">{e.description}</h3>
                            <span className="pt-2 text-right text-xs text-stone-500">
                                {e.id.split("-").slice(-1)}
                            </span>
                        </a>
                        <button
                            onClick={() => openDeleteSystemModal(e.id)}
                            className="absolute top-1 right-1 text-gray-500 hover:text-red-500"
                        >
                            <X />
                        </button>
                    </div>
                ))}
            <button
                onClick={() => setCreate(true)}
                className="h-fill flex flex-col items-center justify-center gap-2 rounded-md bg-stone-100 p-4 hover:bg-stone-200"
            >
                <Plus />
            </button>
            <Modal
                open={showDeleteSystemModal}
                onClose={() => setShowDeleteSystemModal(false)}
            >
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <div className="flex flex-col">
                            <h1 className="font-bold">Confirm</h1>
                            <h3 className="text-sm">Are you sure you want to delete this system?</h3>
                        </div>
                        <ModalClose
                            sx={{
                                position: "relative",
                                top: 0,
                                right: 0,
                            }}
                        />
                    </div>
                    <Divider />
                    <div className="flex flex-row pt-1 gap-4">
                        <Button onClick={() => {setShowDeleteSystemModal(false); setSystemToDelete("");}} variant="outlined" color="neutral">
                            Cancel
                        </Button>
                        <Button onClick={() => handleDeleteSystem(systemToDelete)} variant="solid" color="danger">
                            Confirm
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default ListSystem;
