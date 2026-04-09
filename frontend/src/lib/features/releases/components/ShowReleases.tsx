import { useProjectReleases, type Release } from "$lib/features/releases/queries";
import { Button, Modal, ModalClose, ModalDialog, FormControl, FormLabel, Input, Divider } from "@mui/joy";
import { X } from "lucide-react";
import React, { useState } from "react";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { useMutation } from "@tanstack/react-query";
import FileUpload from "$shared/components/ui/FileUpload";

type Props = {
    project: string;
};

type ReleaseMode = "project" | "file" | "systems";

type ReleaseInput = {
    name: string;
    project: string;
    release_notes: string[];
};

type ImportReleaseInput = ReleaseInput & {
    project_data: unknown;
};

type ImportSystemsReleaseInput = ReleaseInput & {
    systems: Record<string, unknown>[];
};

export const ShowReleases: React.FC<Props> = ({ project }) => {
    const [releases, isSuccessReleases, isLoadingReleases] = useProjectReleases(project);

    const [releaseNotesData, setReleaseNotesData] = useState<string[] | null>(null);
    const [showReleaseNotesModal, setShowReleaseNotesModal] = useState(false);

    const [showNewReleaseModal, setShowNewReleaseModal] = useState(false);
    const [releaseNotes, setReleaseNotes] = useState<string[]>([]);
    const [newNote, setNewNote] = useState("");

    const [mode, setMode] = useState<ReleaseMode>("project");

    const [releaseFileToImport, setReleaseFileToImport] = useState<File | null>(null);
    const [systemsFileToImport, setSystemsFileToImport] = useState<File | null>(null);
    const [importError, setImportError] = useState<string | null>(null);

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
    };

    const closeNewReleaseModal = () => {
        setShowNewReleaseModal(false);
        setReleaseNotes([]);
        setNewNote("");
        setMode("project");
        setReleaseFileToImport(null);
        setSystemsFileToImport(null);
        setImportError(null);
    };

    const handleReleaseFileChange = (file: File | null) => {
        setReleaseFileToImport(file);
        setImportError(null);
    };

    const handleSystemsFileChange = (file: File | null) => {
        setSystemsFileToImport(file);
        setImportError(null);
    };

    const createRelease = useMutation({
        mutationFn: async (releaseInput: ReleaseInput) => {
            try {
                await authAxios.post(`/v1/metadata/releases/`, releaseInput);
                await queryClient.invalidateQueries({ queryKey: ["project", project, "releases"] });
            } catch (error: any) {
                throw new Error(
                    error.response?.data?.detail ||
                    error.response?.data ||
                    "Failed to create release."
                );
            }
        },
    });

    const importRelease = useMutation({
        mutationFn: async (input: ImportReleaseInput) => {
            try {
                await authAxios.post(`/v1/metadata/releases/import/${project}`, input);
                await queryClient.invalidateQueries({ queryKey: ["project", project, "releases"] });
            } catch (error: any) {
                throw new Error(
                    error.response?.data?.detail ||
                    error.response?.data ||
                    "Failed to import release."
                );
            }
        },
    });

    const importSystemsRelease = useMutation({
        mutationFn: async (input: ImportSystemsReleaseInput) => {
            try {
                await authAxios.post(`/v1/metadata/releases/import_systems/${project}/`, input);
                await queryClient.invalidateQueries({ queryKey: ["project", project, "releases"] });
            } catch (error: any) {
                throw new Error(
                    error.response?.data?.detail ||
                    error.response?.data ||
                    "Failed to import systems release."
                );
            }
        },
    });

    const parseJsonFile = async (file: File): Promise<unknown> => {
        const text = await file.text();

        try {
            return JSON.parse(text);
        } catch {
            throw new Error("Invalid JSON file.");
        }
    };

    const isRecordArray = (value: unknown): value is Record<string, unknown>[] => {
        return Array.isArray(value) && value.every(
            (item) => typeof item === "object" && item !== null && !Array.isArray(item)
        );
    };

    const handleProjectRelease = async (name: string) => {
        await createRelease.mutateAsync({ name, project, release_notes: releaseNotes });
    };

    const handleFileRelease = async (name: string) => {
        if (!releaseFileToImport) {
            setImportError("Please choose a JSON file.");
            return false;
        }
        const parsed = await parseJsonFile(releaseFileToImport);
        if (typeof parsed !== "object" || parsed === null || !("project_data" in parsed)) {
            setImportError("Invalid release file format.");
            return false;
        }
        const releaseFile = parsed as { project_data: unknown; release_notes?: string[] };
        await importRelease.mutateAsync({
            name,
            project,
            project_data: releaseFile.project_data,
            release_notes: Array.isArray(releaseFile.release_notes) ? releaseFile.release_notes : [],
        });
        return true;
    };

    const handleSystemsRelease = async (name: string) => {
        if (!systemsFileToImport) {
            setImportError("Please choose a JSON file.");
            return false;
        }
        const parsed = await parseJsonFile(systemsFileToImport);
        if (!isRecordArray(parsed)) {
            setImportError("Invalid systems file format. Expected a JSON array of systems.");
            return false;
        }
        await importSystemsRelease.mutateAsync({
            name,
            project,
            systems: parsed,
            release_notes: releaseNotes,
        });
        return true;
    };

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const rawName = formData.get("name");
        const name = typeof rawName === "string" ? rawName.trim() : "";
        if (!name) return;
        setImportError(null);

        try {
            if (mode === "project") {
                await handleProjectRelease(name);
            } else if (mode === "file") {
                if (!(await handleFileRelease(name))) return;
            } else if (mode === "systems") {
                if (!(await handleSystemsRelease(name))) return;
            }
            closeNewReleaseModal();
        } catch (error) {
            if (error instanceof Error) setImportError(error.message);
            else setImportError("Failed to create or import release.");
        }
    };

    const handleExportRelease = async (release: Release) => {
        const response = await authAxios.get(`/v1/metadata/releases/${release.id}/export/`);
        const jsonStr = JSON.stringify(response.data, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        const releaseDate = new Date(release.created_at);
        const formattedDate = releaseDate.toISOString().slice(0, 16).replace("T", "-");
        const safeName = (release.name || "version").replace(/\s+/g, "_");

        link.href = url;
        link.download = `${safeName}-${formattedDate}.json`;

        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    };

    const handleDeleteRelease = async (releaseId: string) => {
        try {
            await authAxios.delete(`/v1/metadata/releases/${releaseId}/`);
            await queryClient.invalidateQueries({ queryKey: ["project", project, "releases"] });
        } catch {}
    };

    const handleLoadRelease = async (releaseId: string) => {
        await authAxios.post(`/v1/metadata/releases/${releaseId}/load/`, { project });
    };

    if (isLoadingReleases) {
        return <p>Loading releases...</p>;
    }

    const isSubmitting = createRelease.isPending || importRelease.isPending || importSystemsRelease.isPending;

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
                                    <div className="flex justify-end gap-2">
                                        <Button onClick={() => showReleaseNotes(release.release_notes)}>
                                            Release Notes
                                        </Button>

                                        <Button
                                            variant="outlined"
                                            onClick={() => handleExportRelease(release)}
                                        >
                                            Download
                                        </Button>

                                        <Button
                                            color="primary"
                                            variant="solid"
                                            onClick={() => handleLoadRelease(release.id)}
                                        >
                                            Load
                                        </Button>

                                        <Button
                                            color="danger"
                                            variant="solid"
                                            onClick={() => handleDeleteRelease(release.id)}
                                        >
                                            Delete
                                        </Button>
                                    </div>
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
                                <p key={`${note}-${index}`}>
                                    {index + 1}. {note}
                                </p>
                            ))
                        ) : (
                            <p>No release notes available.</p>
                        )}
                    </div>
                </ModalDialog>
            </Modal>

            <Modal open={showNewReleaseModal} onClose={closeNewReleaseModal}>
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <div className="flex flex-col">
                            <h1 className="font-bold">New version</h1>
                            <h3 className="text-sm">
                                {mode === "project" && "Release the current project"}
                                {mode === "file" && "Import a release from file"}
                                {mode === "systems" && "Release current project and attach systems JSON"}
                            </h3>
                        </div>
                        <ModalClose
                            sx={{
                                position: "relative",
                                top: 0,
                                right: 0,
                            }}
                        />
                    </div>

                    <div className="flex flex-row gap-2 pb-4">
                        <Button
                            type="button"
                            variant={mode === "project" ? "solid" : "outlined"}
                            onClick={() => {
                                setMode("project");
                                setImportError(null);
                            }}
                        >
                            From project
                        </Button>

                        <Button
                            type="button"
                            variant={mode === "file" ? "solid" : "outlined"}
                            onClick={() => {
                                setMode("file");
                                setImportError(null);
                            }}
                        >
                            From file
                        </Button>

                        <Button
                            type="button"
                            variant={mode === "systems" ? "solid" : "outlined"}
                            onClick={() => {
                                setMode("systems");
                                setImportError(null);
                            }}
                        >
                            Add systems
                        </Button>
                    </div>

                    <form
                        id="create-release"
                        className="flex min-w-96 flex-col space-y-8"
                        onSubmit={handleSubmit}
                    >
                        <FormControl required>
                            <FormLabel>Name:</FormLabel>
                            <Input name="name" placeholder="v0.0.1" required />
                        </FormControl>

                        {mode !== "file" && (
                            <FormControl>
                                <FormLabel>Version Notes:</FormLabel>

                                {releaseNotes.map((note, index) => (
                                    <div key={`${note}-${index}`} className="flex flex-row gap-4">
                                        <p>
                                            {index + 1}. {note}
                                        </p>
                                        <button
                                            type="button"
                                            onClick={() => handleDeleteReleaseNote(index)}
                                        >
                                            <X />
                                        </button>
                                    </div>
                                ))}

                                <div className="mt-2 flex flex-row gap-2">
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
                        )}

                        {mode === "file" && (
                            <FormControl>
                                <FormLabel>Release JSON file</FormLabel>
                                <FileUpload
                                    accept="application/json,.json"
                                    file={releaseFileToImport}
                                    onFileChange={handleReleaseFileChange}
                                    label="Upload release file"
                                />
                            </FormControl>
                        )}

                        {mode === "systems" && (
                            <FormControl>
                                <FormLabel>Systems JSON file</FormLabel>
                                <FileUpload
                                    accept="application/json,.json"
                                    file={systemsFileToImport}
                                    onFileChange={handleSystemsFileChange}
                                    label="Upload systems file"
                                />
                            </FormControl>
                        )}

                        {importError && <p className="mt-2 text-sm text-red-500">{importError}</p>}
                    </form>

                    <Divider />

                    <div className="flex flex-row pt-1">
                        <Button form="create-release" type="submit" loading={isSubmitting}>
                            {mode === "file" ? "Import version" : "Create version"}
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