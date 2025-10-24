import { authAxios } from "$lib/features/auth/state/auth";
import { useSystemReleases } from "$lib/features/releases/queries";
import { queryClient } from "$shared/hooks/queryClient";
import { Button, CircularProgress, Divider, FormControl, FormLabel, Input, Modal, ModalClose, ModalDialog } from '@mui/joy';
import { useMutation } from "@tanstack/react-query";
import { Rocket, Trash, X } from "lucide-react";
import React, { useState } from "react";
import { useParams } from "react-router";



type Props = {
    system: string;
};

interface Release {
    id: string;
    name: string;
}

export const ShowReleases: React.FC<Props> = ({ system }) => {
    const { systemId } = useParams();
    const [releases, isSuccessReleases, ,] = useSystemReleases(systemId);

    const [showNewReleaseModal, setShowNewReleaseModal] = useState(false);
    const [showLoadReleaseModal, setShowLoadReleaseModal] = useState(false);
    const [loadReleaseObject, setLoadReleaseObject] = useState<Release | undefined>(undefined)
    const [isLoading, setIsLoading] = useState(false);


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

    const [releaseNotesData, setReleaseNotesData] = useState([])
    const [showReleaseNotesDataModal, setShowReleaseNotesDataModal] = useState(false);
    const showReleaseNotes = async (releaseId: string) => {
        try {
            const response = await authAxios.get(`/v1/metadata/releases/${releaseId}`);
            setReleaseNotesData(response.data.release_notes);
            setShowReleaseNotesDataModal(true);

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
    const closeReleaseNotesDataModal = () => {
        setReleaseNotesData([]);
        setShowReleaseNotesDataModal(false);
    }

    const downloadReleaseAsFile = async (release: { id: string; name: string}) => {
        try {
            // Load release metadata as object
            const { data } = await authAxios.get(`/v1/metadata/releases/${release.id}`);
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);

            // Download object as JSON file using a temporary <a> element
            const a = document.createElement("a");
            a.href = url;
            a.download = `${(release.name || "release").replace(/\s+/g, "_")}-${release.id}.json`
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Failed to download release:", err);
        }
    };

    const handleDelete = async (releaseId: string) => {
        try {
            const response = await authAxios.delete(`/v1/metadata/releases/${releaseId}`);
            window.location.reload();
        } catch (error) {
            console.error('Error making request:', error);
        }
    };

    const openLoadModal = async (release) => {
        setLoadReleaseObject(release);
        setShowLoadReleaseModal(true);
    };


    type ReleaseInput = {
        name: string;
        system: string;
        releaseNotes: string[];
    };

    type ReleaseOutput = {
        id: string;
        name: string;
        system: string;
        releaseNotes: string[];
    };
    const { mutateAsync, isPending } = useMutation<
        ReleaseOutput,
        unknown,
        ReleaseInput
    >({
        mutationFn: async (input) => {
            const { name, system, releaseNotes } = input;
            const { data } = await authAxios.post(`v1/metadata/releases/?system_id=${system}&name=${name}&release_notes=${JSON.stringify(releaseNotes)}`);
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
            releaseNotes,
        }).then(() => {
            queryClient.invalidateQueries({ queryKey: ["releases"] });
            authAxios.delete(`/v1/generator/prototypes/system/${systemId}/`);
            close();
            window.location.reload();
        }).catch((err) => {
            console.log(err)
        });
    };

    const handleLoad = async () => {
        setIsLoading(true);
        try {
            const response = await authAxios.post(`/v1/metadata/releases/${loadReleaseObject.id}/load/`);
        } catch (error) {
            console.error('Error making request:', error);
        } finally {
            setLoadReleaseObject(undefined);
            setShowLoadReleaseModal(false);
            setIsLoading(false);
        }
    };

    const [releaseNotes, setReleaseNotes] = useState([]);
    const [newNote, setNewNote] = useState("");

    const handleAddReleaseNote = () => {
        if (newNote.trim()) {
            setReleaseNotes([...releaseNotes, newNote]);
            setNewNote("");
        }
    };

    const handleDeleteReleaseNote = (index: number) => {
        setReleaseNotes(releaseNotes.filter((_, i) => i !== index));
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
                                            onClick={() => showReleaseNotes(e.id)}
                                            className="w-[120px] h-[40px] bg-stone-200 rounded-md hover:bg-stone-300 flex items-center justify-center"
                                        >
                                            Release Notes
                                        </button>
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
                                            onClick={() => downloadReleaseAsFile(e)}
                                            className="w-[100px] h-[40px] bg-stone-200 rounded-md hover:bg-stone-300 flex items-center justify-center"
                                        >
                                            Download
                                        </button>
                                        <button
                                            onClick={() => openLoadModal(e)}
                                            className="w-[70px] h-[40px] bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center justify-center"
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
            <Modal
                open={showReleaseNotesDataModal}
                onClose={closeReleaseNotesDataModal}
            >
                <ModalDialog className="max-h-screen overflow-y-auto">
                    <ModalClose
                        sx={{
                            position: "relative",
                        }}
                    />
                    <div className="flex h-full w-full flex-col gap-1 p-3">
                        <h1 className="font-bold">Release Notes:</h1>
                        {releaseNotesData.map((e, index) => (
                            <div className="flex flex-row gap-4">
                                <p>{index + 1}. {e}</p>
                            </div>
                        ))}
                    </div>
                </ModalDialog>
            </Modal>
            <Modal open={showNewReleaseModal} onClose={() => { close(); setShowNewReleaseModal(false); setReleaseNotes([]); }}>
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
                        className="flex min-w-96 flex-col space-y-8"
                        onSubmit={newRelease}
                    >
                        <FormControl required>
                            <FormLabel>Name:</FormLabel>
                            <Input name="name" placeholder="v0.0.1" required />
                        </FormControl>
                        <FormControl>
                            <FormLabel>Release Notes:</FormLabel>
                            {releaseNotes.map((e, index) => (
                                <div className="flex flex-row gap-4">
                                    <p>{index + 1}. {e}</p>
                                    <button
                                        onClick={() => handleDeleteReleaseNote(index)}
                                    >
                                        <X />
                                    </button>

                                </div>
                            ))}
                            <div className="flex flex-row gap-2 mt-2">
                                <Input
                                    placeholder="Write release note..."
                                    value={newNote}
                                    onChange={(e) => setNewNote(e.target.value)}
                                />
                                <Button variant="outlined" onClick={handleAddReleaseNote}>Add</Button>
                            </div>
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
            {showLoadReleaseModal &&
                <Modal open={showLoadReleaseModal} onClose={() => { close(); setShowLoadReleaseModal(false) }}>
                    <ModalDialog>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <div className="flex flex-col">
                                <h1 className="font-bold">Load a release</h1>
                                <h3 className="text-sm">The diagrams and interfaces from release <b>{loadReleaseObject.name}</b> will be loaded into your work environment</h3>
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
                        <div className="flex flex-col pt-1 w-16">
                            <Button
                                onClick={handleLoad}
                                color="primary"
                                variant="solid"
                                disabled={isLoading} // Disable button if isLoading is true
                            >
                                {isLoading ? (
                                    <div className="flex flex-row gap-2">
                                        <CircularProgress className="animate-spin" />
                                        <p>Loading...</p>
                                    </div>
                                ) : "Load"}
                            </Button>
                        </div>
                        <h3 className="text-sm text-red-500">Warning: this will delete all current changes that have not been released!</h3>
                    </ModalDialog>
                </Modal>
            }
        </>
    );
};

export default ShowReleases;
