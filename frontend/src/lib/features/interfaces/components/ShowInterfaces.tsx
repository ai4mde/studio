import { useAtom } from "jotai";
import { Plus, PaintRoller, X } from "lucide-react";
import React, { useState} from "react";
import { createInterfaceAtom } from "../../browser/atoms";
import { useInterfaces } from "$browser/queries";
import CreateInterface from "./CreateInterface";
import useLocalStorage from './useLocalStorage';
import { authAxios } from "$lib/features/auth/state/auth";
import { useParams } from "react-router";
import { Modal, ModalClose, ModalDialog, Divider, Button } from "@mui/joy";


type Props = {
    system: string;
};

export const ListInterface: React.FC<Props> = ({ system }) => {
    const [, setCreate] = useAtom(createInterfaceAtom);
    const { systemId } = useParams();
    const { data, isSuccess, refetch } = useInterfaces(systemId);
    const [, setStyling, ] = useLocalStorage('styling', '');
    const [, setCategories, ] = useLocalStorage('categories', []);
    const [, setPages, ] = useLocalStorage('pages', []);
    const [, setSections, ] = useLocalStorage('sections', []);
    const [showDeleteInterfaceModal, setShowDeleteInterfaceModal] = useState(false);
    const [interfaceToDelete, setInterfaceToDelete] = useState("");

    const handleLoadInterface = (app_comp) => {

        setStyling(app_comp.styling || {});
        setCategories(app_comp.categories || []);
        setPages(app_comp.pages || []);
        setSections(app_comp.sections || []);
    }

    const generateDefaultInterfaces = async () => {
        try {
            await authAxios.post(`/v1/metadata/interfaces/default?system_id=${systemId}`);
        } catch (error) {
            console.error('Error making request:', error);
        }
        refetch();
    }

    const handleDeleteInterface = async (interfaceId: string) => {
        try {
            await authAxios.delete(`/v1/metadata/interfaces/${interfaceId}`);
        } catch (error) {
            console.error('Error deleting interface:', error);
        } finally {
            setInterfaceToDelete("");
            setShowDeleteInterfaceModal(false);
            refetch();
        }
    }

    const openDeleteInterfaceModal = (interfaceId: string) => {
        setShowDeleteInterfaceModal(true);
        setInterfaceToDelete(interfaceId);
    }

    return (
        <>
            {isSuccess && (
                <div className="flex flex-wrap gap-4">
                    {data.length > 0 ? (
                        data.map((e) => (
                            <div className="relative">
                                <a
                                    key={e.id}
                                    onClick={() => handleLoadInterface(e.data)}
                                    href={`/systems/${system}/interfaces/${e.id}`}
                                    className="flex h-fit w-48 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                                >
                                    <h3 className="text-xl font-bold">{e.name}</h3>
                                    <h3 className="text-sm">{e.description}</h3>
                                    <span className="pt-2 text-right text-xs text-stone-500">
                                        {e.id.split("-").slice(-1)}
                                    </span>
                                </a>
                                <button
                                    onClick={() => openDeleteInterfaceModal(e.id)}
                                    className="absolute top-1 right-1 text-gray-500 hover:text-red-500"
                                >
                                    <X />
                                </button>
                            </div>
                            ))
                    ) : (
                        <button
                            onClick={() => generateDefaultInterfaces()}
                            className="flex h-fit w-30 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                        >
                            <div className="flex flex-row gap-1">
                                <p>Generate default</p>
                                <PaintRoller size={20} />
                            </div>
                        </button>
                )}
                    <button
                        onClick={() => setCreate(true)}
                        className="flex h-fit w-14 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                    >
                        <Plus />
                    </button>
                </div>
            )}
            <CreateInterface system={system} />
            <Modal
                open={showDeleteInterfaceModal}
                onClose={() => setShowDeleteInterfaceModal(false)}
            >
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <div className="flex flex-col">
                            <h1 className="font-bold">Confirm</h1>
                            <h3 className="text-sm">Are you sure you want to delete this interface?</h3>
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
                        <Button onClick={() => {setShowDeleteInterfaceModal(false); setInterfaceToDelete("");}} variant="outlined" color="neutral">
                            Cancel
                        </Button>
                        <Button onClick={() => handleDeleteInterface(interfaceToDelete)} variant="solid" color="danger">
                            Confirm
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default ListInterface;
