import { authAxios } from "$lib/features/auth/state/auth";
import { deletePrototype, deleteSystemPrototypes } from "$lib/features/prototypes/mutations";
import { useSystemPrototypes } from "$lib/features/prototypes/queries";
import { prototypeURL } from "$shared/globals";
import { Button, CircularProgress, Divider, Modal, ModalClose, ModalDialog } from '@mui/joy';
import { useQueryClient } from "@tanstack/react-query";
import { Package, Trash } from "lucide-react";
import React, { useEffect, useState } from "react";
import { useParams } from "react-router";


type Props = {
    system: string;
};

export const ShowPrototypes: React.FC<Props> = ({ system }) => {
    const { systemId } = useParams();
    const [data, isSuccess] = useSystemPrototypes(systemId);
    const [prototypeStatuses, setPrototypeStatuses] = useState<{ [key: string]: string }>({});
    const [showModal, setShowModal] = useState(false);
    const [loading, setLoading] = useState<{ [key: string]: boolean }>({});
    const [metadata, setMetadata] = useState("");
    const [showMetadataModal, setShowMetadataModal] = useState(false);

    const queryClient = useQueryClient();
    useEffect(() => {
        queryClient.invalidateQueries(["prototypes", systemId]);
    }, [queryClient, systemId]);

    useEffect(() => {
        const fetchActivePrototype = async () => {
            try {
                const response = await authAxios.get(`/v1/generator/prototypes/active_prototype/`);
                const activePrototypeId = response.data.prototype_id;
                const isRunning = response.data.running;

                if (data) {
                    setPrototypeStatuses(() =>
                        data.reduce((statuses, prototype) => {
                            statuses[prototype.id] =
                                isRunning && prototype.id === activePrototypeId ? "Running" : "Not running";
                            return statuses;
                        }, {})
                    );
                }
            } catch (error) {
                console.error('Error fetching active prototype:', error);
            }
        };

        fetchActivePrototype();
        const intervalId = setInterval(fetchActivePrototype, 5000);

        return () => clearInterval(intervalId);
    }, [data]);


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
    };

    const openModal = () => {
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
    };

    const proceedDeleteAll = async () => {
        closeModal();
        await handleDeleteAll();
    };

    const handleRun = async (prototypeId: string) => {
        setLoading((prev) => ({ ...prev, [prototypeId]: true }));
        try {
            await authAxios.post(`/v1/generator/prototypes/run/${prototypeId}`);
        } catch (error) {
            console.error('Error making run request:', error);
        } finally {
            setTimeout(() => {
                setLoading((prev) => ({ ...prev, [prototypeId]: false }));
            }, 6000);
        }
    };

    const handleStop = async (prototypeId: string) => {
        setLoading((prev) => ({ ...prev, [prototypeId]: true }));
        try {
            await authAxios.post(`/v1/generator/prototypes/stop_prototypes/`);
        } catch (error) {
            console.error('Error making stop request:', error);
        } finally {
            setTimeout(() => {
                setLoading((prev) => ({ ...prev, [prototypeId]: false }));
            }, 6000);
        }
    };

    const showMetadata = async (prototypeId: string) => {
        try {
            const response = await authAxios.get(`/v1/generator/prototypes/${prototypeId}/meta`);
            setMetadata(response.data);
            setShowMetadataModal(true);

        } catch (error) {
            console.error('Error making request:', error);
        }
    }

    const closeMetadataModal = () => {
        setMetadata("");
        setShowMetadataModal(false);
    }

    return (
        <>
            <table className="min-w-full bg-white text-left">
                <thead className="text-sm w-full">
                    <tr>
                        <th className="py-2 px-4 text-left border-b border-stone-200 w-30">
                            <span className="flex flex-row items-center gap-2">
                                <Package size={24} />
                                <h1 className="text-lg">Prototypes</h1>
                            </span>
                        </th>
                        <th className="py-2 px-4 text-left border-b border-stone-200 w-52">Status</th>
                        <th className="py-2 px-4 text-left border-b border-stone-200 w-52">URL</th>
                        <th className="py-2 px-4 text-left border-b border-stone-200 w-40 text-right">
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
                {isSuccess && (
                    <tbody className="max-h-96 overflow-y-auto">
                        {[...data].reverse().map((e, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                                <td className="py-2 px-4 text-left border-b border-gray-200">
                                    <h1 className="text-lg">{e.name}</h1>
                                    <h2 className="text-stone-400">{e.description}</h2>
                                </td>
                                <td className="py-2 px-4 text-left border-b border-gray-200">
                                    {prototypeStatuses[e.id] || (
                                        <CircularProgress className="animate-spin" />
                                    )}
                                </td>
                                <td className="py-2 px-4 text-left border-b border-gray-200">
                                    {(prototypeStatuses[e.id] === "Running") &&
                                        <a href={prototypeURL} target="_blank" className="text-blue-500 hover:underline">
                                            {prototypeURL}
                                        </a>
                                    }
                                </td>
                                <td className="py-2 px-4 text-left border-b border-gray-200 w-60 flex space-x-2">
                                    <button
                                        onClick={() => showMetadata(e.id)}
                                        className="w-[100px] h-[40px] bg-stone-200 rounded-md hover:bg-stone-300 flex items-center justify-center"
                                    >
                                        Metadata
                                    </button>
                                    {prototypeStatuses[e.id] === "Running" && (
                                        <button
                                            onClick={() => handleStop(e.id)}
                                            disabled={loading[e.id]}
                                            className={`w-[60px] h-[40px] rounded-md ${loading[e.id] ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600'
                                                } text-white`}
                                        >
                                            Kill
                                        </button>
                                    )}
                                    {prototypeStatuses[e.id] === "Not running" && (
                                        <button
                                            onClick={() => handleRun(e.id)}
                                            disabled={loading[e.id]}
                                            className={`w-[60px] h-[40px] rounded-md ${loading[e.id] ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600'
                                                } text-white`}
                                        >
                                            Run
                                        </button>
                                    )}
                                    <button
                                        onClick={() => handleDelete(e.id)}
                                        className="w-[40px] h-[40px] bg-red-500 text-white rounded-md hover:bg-red-600 flex items-center justify-center"
                                    >
                                        <Trash />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                )}
            </table>

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
            <Modal
                open={showMetadataModal}
                onClose={closeMetadataModal}
            >
                <ModalDialog className="max-h-screen overflow-y-auto">
                    <ModalClose
                        sx={{
                            position: "relative",
                        }}
                    />
                    <div className="flex h-full w-full flex-col gap-1 p-3">
                        <pre>{JSON.stringify(metadata, null, 2)}</pre>
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default ShowPrototypes;
