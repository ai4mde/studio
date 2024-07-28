import React, { useState, useEffect } from "react";
import { Package, Trash } from "lucide-react";
import { useParams } from "react-router";
import { useSystemPrototypes } from "$lib/features/prototypes/queries";
import { deletePrototype, deleteSystemPrototypes } from "$lib/features/prototypes/mutations";
import { Button, Modal, ModalDialog, ModalClose, Divider } from '@mui/joy';

type Props = {
    system: string;
};

export const ShowPrototypes: React.FC<Props> = ({ system }) => {
    const { systemId } = useParams();
    const [data, isSuccess] = useSystemPrototypes(systemId);
    const [showModal, setShowModal] = useState(false);

    const handleDelete = async (prototypeId: string) => {
        try {
            await deletePrototype(prototypeId);
            window.location.reload();
        } catch (error) {
            console.error('Error deleting prototype:', error);
        }
    };

    const handleDeleteAll = async () => {
        try {
            await deleteSystemPrototypes(systemId);
            window.location.reload();
        } catch (error) {
            console.error('Error deleting prototypes:', error);
        }
    }

    const openModal = () => {
        setShowModal(true);
    }

    const closeModal = () => {
        setShowModal(false);
    }

    const proceedDeleteAll = async () => {
        closeModal();
        await handleDeleteAll();
    }

    return (
        <>
            <table className="min-w-full bg-white text-left">
                <thead className="text-sm">
                    <tr>
                        <th className="py-2 px-4 border-b border-stone-200">
                            <span className="flex flex-row items-center gap-2">
                                <Package size={24} />
                                <h1 className="text-lg">Prototypes</h1>
                            </span>
                        </th>
                        <th className="py-2 px-4 border-b border-stone-200">Status</th>
                        <th className="py-2 px-4 border-b border-stone-200">URL</th>
                        <th className="w-40 py-2 px-4 border-b border-stone-200">
                            <Button
                                onClick={openModal}
                                color="danger"
                                variant="solid"
                                className="w-[110px] h-[40px]"
                            >
                                <h2 className="text-base">Delete all</h2>
                            </Button>
                        </th>
                    </tr>
                </thead>
            </table>
            {isSuccess && (
                <div className="max-h-96 overflow-y-auto">
                    <table className="min-w-full bg-white text-left">
                        <tbody>
                            {[...data].reverse().map((e, index) => (
                                <tr key={index} className="hover:bg-gray-50">
                                    <td className="py-2 px-4 border-b border-gray-200">
                                        <h1 className="text-lg">{e.name}</h1>
                                        <h2 className="text-stone-400">{e.description}</h2>
                                    </td>
                                    <td className="py-2 px-4 border-b border-gray-200">
                                        {e.status}
                                    </td>
                                    <td className="py-2 px-4 border-b border-gray-200">
                                        <a href={e.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                                            {e.url}
                                        </a>
                                    </td>
                                    <td className="w-20 py-2 px-4 border-b border-gray-200">
                                        <button
                                            onClick={() => handleDelete(e.id)}
                                            className="w-[40px] h-[40px] bg-red-500 text-white px-2 py-1 rounded-md hover:bg-red-600"
                                        >
                                            <Trash />
                                        </button>
                                        
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            <Modal
                open={showModal}
                onClose={closeModal}
            >
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                    <div className="flex flex-col">
                        <h1 className="font-bold">Confirm</h1>
                        <h3 className="text-sm">Are you sure you want to delete all prototypes in this system?</h3>
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
                        <Button onClick={closeModal} variant="outlined" color="neutral">
                            Cancel
                        </Button>
                        <Button onClick={proceedDeleteAll} variant="solid" color="danger">
                            Confirm
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default ShowPrototypes;
