import React, { useEffect, useState } from "react";
import { useAtom } from "jotai";
import { useMutation } from "@tanstack/react-query";
import CryptoJS from 'crypto-js';
import {
    Button,
    CircularProgress,
    Divider,
    FormControl,
    FormLabel,
    Input,
    Modal,
    ModalClose,
    ModalDialog,
    Switch,
    Typography
} from "@mui/joy";
import { useParams } from "react-router";
import Select from "react-select";
import { queryClient } from "$shared/hooks/queryClient";
import { authAxios } from "$lib/features/auth/state/auth";
import { createPrototypeAtom } from "$lib/features/prototypes/atoms";
import { useSystemInterfaces, useSystemDiagrams } from "$lib/features/prototypes/queries";
import { useQueryClient } from "@tanstack/react-query";

type PrototypeInput = {
    name: string;
    description?: string;
    system: string;
    running?: boolean;
    metadata: Record<string, any>;
    database_hash?: string;
};

type PrototypeOutput = {
    id: string;
    name: string;
    description: string;
    system: string;
    running: boolean;
};

export const CreatePrototype: React.FC = () => {
    const [open, setOpen] = useAtom(createPrototypeAtom);
    const close = () => setOpen(false);
    const { systemId } = useParams();
    const [interfaces, isSuccessInterfaces] = useSystemInterfaces(systemId);
    const [diagrams, isSuccessDiagrams] = useSystemDiagrams(systemId);
    const [selectedInterfaces, setSelectedInterfaces] = useState([]);
    const [error, setError] = useState<string | null>(null);
    const [generationError, setGenerationError] = useState<string | null>(null);
    const [useAuthentication, setUseAuthentication] = useState(true);
    const [databaseHash, setDatabaseHash] = useState<string | null>(null);
    const [databasePrototypes, setDatabasePrototypes] = useState([]);
    const [selectedDatabasePrototype, setSelectedDatabasePrototype] = useState(null);

    useEffect(() => {
        if (isSuccessInterfaces && interfaces) {
            setSelectedInterfaces(interfaces.map((e) => ({ label: e.name, value: e})));
        }
    }, [interfaces, isSuccessInterfaces]);

    useEffect(() => {
        const computeHash = async () => {
            if (systemId && isSuccessInterfaces) {
                const [classifiers, relations] = await Promise.all([
                    authAxios.get(`v1/metadata/systems/${systemId}/classes/`),
                    authAxios.get(`v1/metadata/systems/${systemId}/classifier-relations/`),
                ]);

                const interfaceNames = interfaces.map((e) => ({ name: e.name }));
                const inputString = `${systemId}${JSON.stringify(classifiers.data)}${JSON.stringify(relations.data)}${JSON.stringify(interfaceNames)}`;
                const hash = CryptoJS.SHA256(inputString).toString(CryptoJS.enc.Hex);
                setDatabaseHash(hash);
            }
        };

        computeHash();
    }, [systemId, interfaces, isSuccessInterfaces]);

    useEffect(() => {
        const fetchDatabasePrototypes = async () => {
            if (databaseHash) {
                try {
                    const { data } = await authAxios.get(`v1/generator/prototypes/${databaseHash}`);
                    setDatabasePrototypes(data.map((e) => ({ label: e.name, value: e })));
                } catch (error) {
                    console.error("Failed to fetch database prototypes:", error);
                }
            }
        };

        fetchDatabasePrototypes();
    }, [databaseHash]);

    const { mutateAsync, isPending } = useMutation<
        PrototypeOutput,
        unknown,
        PrototypeInput
    >({
        mutationFn: async (input) => {
            const { name, description, system, metadata } = input;
            if (selectedDatabasePrototype) {
                const { data } = await authAxios.post(`v1/generator/prototypes/?database_prototype_name=${selectedDatabasePrototype.label}`, {
                    name,
                    description,
                    system_id: system,
                    metadata,
                    database_hash: databaseHash,
                });
                return data
            }
            else {
                const { data } = await authAxios.post(`v1/generator/prototypes/?database_prototype_name=`, {
                    name,
                    description,
                    system_id: system,
                    metadata,
                    database_hash: databaseHash,
                });
                return data
            }

        },
        onError: (error) => {
            setGenerationError("An error occurred while creating the prototype!");
        },
    });

    const queryClient = useQueryClient();
    const onSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
        e.preventDefault();
        setError(null);

        const formData = new FormData(e.currentTarget);
        const name = `${formData.get("name")}`.trim();
        const description = `${formData.get("description")}`;
        const running = Boolean(`${formData.get("running")}`);
        const metadata = {
            "diagrams": diagrams,
            "interfaces": selectedInterfaces,
            "useAuthentication": useAuthentication,
        };

        const alphanumericRegex = /^[a-zA-Z0-9]+$/;
        if (!alphanumericRegex.test(name)) {
            setError("Name may only contain alphanumeric characters!");
            return;
        }

        if (!databaseHash) {
            setError("No database hash.");
            return;
        }

        mutateAsync({
            name,
            description,
            system: systemId || "",
            running,
            metadata,
            database_hash: databaseHash,
        }).then(() => {
            queryClient.invalidateQueries(["prototypes", systemId]); 
            close();
        }).catch((err) => {
            console.log(err)
        });
    };

    if (isPending) {
        return (
            <Modal open>
                <ModalDialog className="flex flex-row items-center gap-2">
                    <CircularProgress className="animate-spin" />
                    <Typography>
                        <h1 className="text-lg">Generating...</h1>
                    </Typography>
                </ModalDialog>
            </Modal>
        );
    }

    return (
        <Modal open={open} onClose={() => {close(); setGenerationError(null)}}>
            <ModalDialog>
                <div className="flex w-full flex-row justify-between pb-1">
                    <div className="flex flex-col">
                        <h1 className="font-bold">Generate Prototype</h1>
                        <h3 className="text-sm">Generate a new prototype using current metadata</h3>
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
                <form
                    id="create-project"
                    className="flex min-w-96 flex-col gap-2"
                    onSubmit={onSubmit}
                >
                    <FormControl required>
                        <FormLabel>Name</FormLabel>
                        <Input name="name" placeholder="Prototype" required />
                        {error && (
                            <Typography sx={{ margin: '2px' }}>
                                <h1 className="text-sm text-red-400">{error}</h1>
                            </Typography>
                        )}
                    </FormControl>
                    <FormControl>
                        <FormLabel>Description</FormLabel>
                        <Input
                            name="description"
                            placeholder="A whole new world..."
                        />
                    </FormControl>
                    <FormControl>
                        <FormLabel>Interfaces</FormLabel>
                        <Select
                            isMulti
                            name="interfaces"
                            options={interfaces.map((e) => ({ label: e.name, value: e}))}
                            value={selectedInterfaces}
                            onChange={setSelectedInterfaces}
                        />
                    </FormControl>
                    <FormControl>
                        <FormLabel>Reuse database</FormLabel>
                        <Select
                            name="database"
                            options={databasePrototypes}
                            value={selectedDatabasePrototype}
                            onChange={setSelectedDatabasePrototype}
                        />
                    </FormControl>
                    <FormControl>
                        <span className="flex flex-row items-center gap-2">
                            <Switch 
                                defaultChecked={useAuthentication} 
                                onChange={(e) => setUseAuthentication(e.target.checked)} 
                            />
                            <FormLabel sx={{ marginTop: '4px' }}>Use Authentication</FormLabel>
                        </span>
                    </FormControl>
                </form>
                <Divider />
                <div className="flex flex-row pt-1">
                    <Button form="create-project" type="submit" disabled={isPending}>
                        {isPending ? 
                        <div className="flex flex-row gap-2">
                            <CircularProgress className="animate-spin" />
                            <p>Generating</p>
                        </div> : "Create"}
                    </Button>
                </div>
                {generationError && (
                    <Typography sx={{ margin: '2px' }}>
                        <h1 className="text-lg text-red-800">{generationError}</h1>
                    </Typography>
                )}
            </ModalDialog>
        </Modal>
    );
};

export default CreatePrototype;
