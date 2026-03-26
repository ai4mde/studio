import { useProjectReleases } from "$lib/features/releases/queries";
import { Button, Modal, ModalClose, ModalDialog, FormControl, FormLabel, Input, Divider } from "@mui/joy";
import { X } from 'lucide-react';
import React, { useState } from "react";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { useMutation } from "@tanstack/react-query";



type Props = {
    project: string;
};

type ReleaseInput = {
    name: string
    project: string
    release_notes: string[]
}

export const ShowReleases: React.FC<Props> = ({ project }) => {
    const [releases, isSuccessReleases, isLoadingReleases] = useProjectReleases(project);

    const [releaseNotesData, setReleaseNotesData] = useState<string[] | null>(null);
    const [showReleaseNotesModal, setShowReleaseNotesModal] = useState(false);

    const [showNewReleaseModal, setShowNewReleaseModal] = useState(false);
    const [releaseNotes, setReleaseNotes] = useState<string[]>([]);
    const [newNote, setNewNote] = useState("");

    const showReleaseNotes = (notes: string[]) => {
        setReleaseNotesData(notes);
        setShowReleaseNotesModal(true);
    };

    const closeReleaseNotes = () => {
        setReleaseNotesData(null);
        setShowReleaseNotesModal(false);
    };

    const handleAddReleaseNote = () => {
        if (newNote.trim() === "") return;
        setReleaseNotes([...releaseNotes, newNote.trim()]);
        setNewNote("");
    };

    const handleDeleteReleaseNote = (index: number) => {
        setReleaseNotes(releaseNotes.filter((_, i) => i !== index));
    }

    const { mutateAsync, isPending } = useMutation({
        mutationFn: async (releaseInput: ReleaseInput) => {
            await authAxios.post(`/v1/metadata/releases/`, releaseInput);
            queryClient.invalidateQueries({ queryKey: ["project", project, "releases"] });
        },
    });

    // TODO: connect mutation to form

    if (isLoadingReleases) {
        return <p>Loading releases...</p>;
    }

        return (
        <>
            <table className="min-w-full bg-white text-left">
                <thead>
                    <tr>
                        <th className="py-2 px-4 border-b">Name</th>
                        <th className="py-2 px-4 border-b">Created at</th>
                        <th className="py-2 px-4 border-b"></th>
                    </tr>
                </thead>
                <tbody>
                    {isSuccessReleases && releases.length > 0 ? (
                        [...releases].reverse().map((release) => (
                            <tr key={release.id}>
                                <td className="py-2 px-4 border-b">{release.name}</td>
                                <td className="py-2 px-4 border-b">{release.created_at}</td>
                                <td className="py-2 px-4 border-b text-right">
                                    <Button onClick={() => showReleaseNotes(release.release_notes)}>
                                        Release Notes
                                    </Button>
                                </td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan={3} className="py-4 px-4 text-center">
                                No releases found
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
            <button
                className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fill items-center justify-center"
                onClick={() => setShowNewReleaseModal(true)}
            >
                New version
            </button>

            <Modal open={showReleaseNotesModal} onClose={closeReleaseNotes}>
                <ModalDialog>
                    <ModalClose />
                    <div className="flex flex-col gap-2 p-2">
                        <h2 className="font-bold text-lg">Release Notes</h2>
                        {releaseNotesData && releaseNotesData.length > 0 ? (
                            releaseNotesData.map((note, index) => (
                                <p key={index}>
                                    {index + 1}. {note}
                                </p>
                            ))
                        ) : (
                            <p>No release notes available.</p>
                        )}
                    </div>
                </ModalDialog>
            </Modal>

            <Modal
                open={showNewReleaseModal}
                onClose={() => {
                    setShowNewReleaseModal(false);
                    setReleaseNotes([]);
                    setNewNote("");
                }}
            >
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <div className="flex flex-col">
                            <h1 className="font-bold">New version</h1>
                            <h3 className="text-sm">Release the current project</h3>
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
                    >
                        <FormControl required>
                            <FormLabel>Name:</FormLabel>
                            <Input name="name" placeholder="v0.0.1" required />
                        </FormControl>

                        <FormControl>
                            <FormLabel>Version Notes:</FormLabel>

                            {releaseNotes.map((note, index) => (
                                <div key={index} className="flex flex-row gap-4">
                                    <p>{index + 1}. {note}</p>
                                    <button
                                        type="button"
                                        onClick={() => handleDeleteReleaseNote(index)}
                                    >
                                        <X />
                                    </button>
                                </div>
                            ))}

                            <div className="flex flex-row gap-2 mt-2">
                                <Input
                                    placeholder="Write version note..."
                                    value={newNote}
                                    onChange={(e) => setNewNote(e.target.value)}
                                />
                                <Button
                                    type="button"
                                    variant="outlined"
                                    onClick={handleAddReleaseNote}
                                >
                                    Add
                                </Button>
                            </div>
                        </FormControl>
                    </form>

                    <Divider />

                    <div className="flex flex-row pt-1">
                        <Button form="create-release" type="submit">
                            Version
                        </Button>
                    </div>

                    <h3 className="text-sm text-red-500">
                        Warning: this will delete all prototypes of this system!
                    </h3>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default ShowReleases;
