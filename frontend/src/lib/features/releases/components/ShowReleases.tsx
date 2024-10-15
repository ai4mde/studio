import { authAxios } from "$lib/features/auth/state/auth";
import { useSystemReleases } from "$lib/features/releases/queries";
import { queryClient } from "$shared/hooks/queryClient";
import { Button, CircularProgress, Divider, FormControl, FormLabel, Input, Modal, ModalClose, ModalDialog } from '@mui/joy';
import { useMutation } from "@tanstack/react-query";
import { Rocket, Trash } from "lucide-react";
import React, { useState } from "react";
import { useParams } from "react-router";



type Props = {
    system: string;
};

export const ShowReleases: React.FC<Props> = ({ system }) => {
    const { systemId } = useParams();
    const [releases, isSuccessReleases, ,] = useSystemReleases(systemId);

    const [showNewReleaseModal, setShowNewReleaseModal] = useState(false);

    const [diagramsData, setDiagramsData] = useState("")
    const [showDiagramsDataModal, setShowDiagramsDataModal] = useState(false);
    const showDiagrams = async (releaseId: string) => {
        try {
            const response = await authAxios.get(`/v1/metadata/releases/${releaseId}`);
            setDiagramsData(response.data.diagrams);
            setShowDiagramsDataModal(true);

        } catch (error) {
            console.error('Error making request:', error);
        }
    };

    const closeDiagramsDataModal = () => {
        setDiagramsData("");
        setShowDiagramsDataModal(false);
    }

    const [interfacesData, setInterfacesData] = useState("")
    const [showInterfacesDataModal, setShowInterfacesDataModal] = useState(false);
    const showInterfaces = async (releaseId: string) => {
        try {
            const response = await authAxios.get(`/v1/metadata/releases/${releaseId}`);
            setInterfacesData(response.data.interfaces);
            setShowInterfacesDataModal(true);

        } catch (error) {
            console.error('Error making request:', error);
        }
    };

    const closeInterfacesDataModal = () => {
        setInterfacesData("");
        setShowInterfacesDataModal(false);
    }

    const handleDelete = async (releaseId: string) => {
        try {
            const response = await authAxios.delete(`/v1/metadata/releases/${releaseId}`);
            window.location.reload();
        } catch (error) {
            console.error('Error making request:', error);
        }
    };

    const handleLoad = async (releaseId: string) => {

    };


    type ReleaseInput = {
        name: string;
        system: string;
    };

    type ReleaseOutput = {
        id: string;
        name: string;
        system: string;
    };
    const { mutateAsync, isPending } = useMutation<
        ReleaseOutput,
        unknown,
        ReleaseInput
    >({
        mutationFn: async (input) => {
            const { name, system } = input;
            const { data } = await authAxios.post(`v1/metadata/releases/?system_id=${system}&name=${name}`);
            return data
        },
    });

    const newRelease: React.FormEventHandler<HTMLFormElement> = async (e) => {
        e.preventDefault();

        const formData = new FormData(e.currentTarget);
        const name = `${formData.get("name")}`;

        mutateAsync({
            name,
            system: systemId || "",
        }).then(() => {
            queryClient.invalidateQueries({ queryKey: ["releases"] });
            authAxios.delete(`/v1/generator/prototypes/system/${systemId}/`);
            close();
            window.location.reload();
        }).catch((err) => {
            console.log(err)
        });
    };


    return (
        <>
            <table className="min-w-full bg-white text-left">
                <thead className="text-sm w-full">
                    <tr>
                        <th className="py-2 px-4 text-left border-b border-stone-200 w-30">
                            <span className="flex flex-row items-center gap-2">
                                <Rocket size={24} />
                                <h1 className="text-lg">Releases</h1>
                            </span>
                        </th>
                        <th className="py-2 px-4 text-left border-b border-stone-200 w-52">Date</th>
                        <th className="py-2 px-4 text-left border-b border-stone-200 w-52"></th>
                    </tr>
                </thead>
                <tbody className="max-h-96 overflow-y-auto">
                    {isSuccessReleases && (
                        [...releases].reverse().map((e, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                                <td className="py-2 px-4 text-left border-b border-gray-200">
                                    <h1 className="text-lg">{e.name}</h1>
                                </td>
                                <td className="py-2 px-4 text-left border-b border-gray-200">
                                    <h1 className="text-lg">{e.created_at}</h1>
                                </td>
                                <td className="py-2 px-4 text-right border-b border-gray-200 w-full">
                                    <div className="flex justify-end space-x-2">
                                        <button
                                            onClick={() => showDiagrams(e.id)}
                                            className="w-[100px] h-[40px] bg-stone-200 rounded-md hover:bg-stone-300 flex items-center justify-center"
                                        >
                                            Diagrams
                                        </button>
                                        <button
                                            onClick={() => showInterfaces(e.id)}
                                            className="w-[100px] h-[40px] bg-stone-200 rounded-md hover:bg-stone-300 flex items-center justify-center"
                                        >
                                            Interfaces
                                        </button>
                                        <button
                                            onClick={() => handleLoad(e.id)}
                                            disabled
                                            className="w-[70px] h-[40px] bg-blue-500 text-white rounded-md hover:cursor-not-allowed flex items-center justify-center"
                                        >
                                            Load
                                        </button>
                                        <button
                                            onClick={() => handleDelete(e.id)}
                                            className="w-[40px] h-[40px] bg-red-500 text-white rounded-md hover:bg-red-600 flex items-center justify-center"
                                        >
                                            <Trash />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
            <button
                className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fill items-center justify-center"
                onClick={() => setShowNewReleaseModal(true)}
            >
                New release
            </button>
            <Modal
                open={showDiagramsDataModal}
                onClose={closeDiagramsDataModal}
            >
                <ModalDialog className="max-h-screen overflow-y-auto">
                    <ModalClose
                        sx={{
                            position: "relative",
                        }}
                    />
                    <div className="flex h-full w-full flex-col gap-1 p-3">
                        <pre>{JSON.stringify(diagramsData, null, 2)}</pre>
                    </div>
                </ModalDialog>
            </Modal>
            <Modal
                open={showInterfacesDataModal}
                onClose={closeInterfacesDataModal}
            >
                <ModalDialog className="max-h-screen overflow-y-auto">
                    <ModalClose
                        sx={{
                            position: "relative",
                        }}
                    />
                    <div className="flex h-full w-full flex-col gap-1 p-3">
                        <pre>{JSON.stringify(interfacesData, null, 2)}</pre>
                    </div>
                </ModalDialog>
            </Modal>
            <Modal open={showNewReleaseModal} onClose={() => { close(); setShowNewReleaseModal(false) }}>
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <div className="flex flex-col">
                            <h1 className="font-bold">New release</h1>
                            <h3 className="text-sm">Release the current diagrams & metadata</h3>
                        </div>
                        <ModalClose
                            sx={{
                                position: "relative",
                                top: 0,
                                right: 0,
                            }}
                        />
                    </div>
                    <form
                        id="create-release"
                        className="flex min-w-96 flex-col gap-2"
                        onSubmit={newRelease}
                    >
                        <FormControl required>
                            <FormLabel>Name</FormLabel>
                            <Input name="name" placeholder="v0.0.1" required />
                        </FormControl>
                    </form>
                    <Divider />
                    <div className="flex flex-row pt-1">
                        <Button form="create-release" type="submit" disabled={isPending}>
                            {isPending ?
                                <div className="flex flex-row gap-2">
                                    <CircularProgress className="animate-spin" />
                                    <p>Releasing...</p>
                                </div> : "Release"}
                        </Button>
                    </div>
                    <h3 className="text-sm text-red-500">Warning: this will delete all prototypes of this system!</h3>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default ShowReleases;
