import { createPrototypeAtom } from "$lib/features/prototypes/atoms";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
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
import { useMutation } from "@tanstack/react-query";
import { useAtom } from "jotai";
import React, { useEffect, useState } from "react";
import Select from "react-select";
import { useParams } from "react-router";
import { useSystemInterfaces, useSystemDiagrams } from "$lib/features/prototypes/queries";

type PrototypeInput = {
    name: string;
    description?: string;
    system: string;
    running?: boolean;
    metadata: Record<string, any>;
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


    useEffect(() => {
        if (isSuccessInterfaces && interfaces) {
            setSelectedInterfaces(interfaces.map((e) => ({ label: e.name, value: e})));
        }
    }, [interfaces, isSuccessInterfaces]);

    const { mutateAsync, isPending } = useMutation<
        PrototypeOutput,
        unknown,
        PrototypeInput
    >({
        mutationFn: async ({ name, description, running }) => {
            const metadata = {
                "diagrams": diagrams,
                "interfaces": selectedInterfaces,
                "useAuthentication": useAuthentication,
            };
            const { data } = await authAxios.post("v1/generator/prototypes/", {
                name: name,
                description: description,
                system_id: systemId,
                running: running,
                metadata: metadata,
            });

            return data;
        },
        onError: (error) => {
            setGenerationError("An error occurred while creating the prototype!");
        },
    });

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
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

        mutateAsync({
            name,
            description,
            system: systemId || "",
            running,
            metadata,
        }).then(() => {
            queryClient.invalidateQueries({ queryKey: ["prototypes"] });
            close();
            window.location.reload();
        }).catch((err) => {
        });
    };

    if (isPending) {
        return (
            <Modal open>
                <ModalDialog>
                    <CircularProgress className="animate-spin" />
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
