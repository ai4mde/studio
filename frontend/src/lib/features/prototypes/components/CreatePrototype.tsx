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
} from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { useAtom } from "jotai";
import React, { useEffect, useState } from "react";
import Select from "react-select";
import { useParams } from "react-router";
import { useSystemInterfaces } from "$lib/features/prototypes/queries";



type PrototypeInput = {
    name: string;
    description?: string;
    system: string;
    running?: boolean;
    interfaces: string;
};

type PrototypeOutput = {
    id: string;
    name: string;
    description: string;
    system: string;
    running: boolean;
    interfaces: string;
};

export const CreatePrototype: React.FC = () => {
    const [open, setOpen] = useAtom(createPrototypeAtom);
    const close = () => setOpen(false);
    const { systemId } = useParams();
    const [interfaces, isSuccessInterfaces] = useSystemInterfaces(systemId);
    const [selectedInterfaces, setSelectedInterfaces] = useState([]);

    useEffect(() => {
        if (isSuccessInterfaces && interfaces) {
            setSelectedInterfaces(interfaces.map((e) => ({ label: e.name, value: e.name })));
        }
    }, [interfaces, isSuccessInterfaces]);


    const { mutateAsync, isPending } = useMutation<
        PrototypeOutput,
        unknown,
        PrototypeInput
    >({
        mutationFn: async ({ name, description, running, interfaces }) => {
            const { data } = await authAxios.post("v1/generator/prototypes/", {
                name: name,
                description: description,
                system: systemId,
                running: running,
                interfaces: interfaces,
            });

            return data;
        },
    });

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);

        mutateAsync({
            name: `${formData.get("name")}`,
            description: `${formData.get("description")}`,
            system: systemId || "",
            running: Boolean(`${formData.get("running")}`),
            interfaces: `${formData.get("interfaces")}`,
        }).then(() => {
            queryClient.invalidateQueries({ queryKey: ["protoypes"] });
            close();
        });
    };

    if (isPending) {
        <Modal open>
            <ModalDialog>
                <CircularProgress className="animate-spin" />
            </ModalDialog>
        </Modal>;
    }

    return (
        <Modal open={open} onClose={() => close()}>
            <ModalDialog>
                <div className="flex w-full flex-row justify-between pb-1">
                    <div className="flex flex-col">
                        <h1 className="font-bold">Generate Protype</h1>
                        <h3 className="text-sm">Generate a new project using current metadata</h3>
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
                            options={interfaces.map((e) => ({ label: e.name, value: e.name }))}
                            value={selectedInterfaces}
                            onChange={setSelectedInterfaces}
                        />
                    </FormControl>
                    <FormControl>
                        <span className="flex flex-row items-center gap-2">
                            <Switch defaultChecked />
                            <FormLabel sx={{ marginTop: '4px' }}>Use Authentication</FormLabel>
                        </span>
                    </FormControl>
                </form>
                <Divider />
                <div className="flex flex-row pt-1">
                    <Button form="create-project" type="submit">
                        Create
                    </Button>
                </div>
            </ModalDialog>
        </Modal>
    );
};

export default CreatePrototype;
