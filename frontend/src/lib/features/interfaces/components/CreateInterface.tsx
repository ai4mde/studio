import { createInterfaceAtom } from "$browser/atoms";
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
} from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { useAtom } from "jotai";
import React, { useState } from "react";
import Select from "react-select";
import { useParams } from "react-router";
import { useSystemActors } from "$lib/features/interfaces/queries";



type InterfaceInput = {
    name: string;
    description?: string;
    actor: string;
};

type InterfaceOutput = {
    id: string;
    name: string;
    description: string;
    actor: string;
};

type Props = {
    system: string;
};

export const CreateInterface: React.FC<Props> = ({ system }) => {
    const [open, setOpen] = useAtom(createInterfaceAtom);
    const close = () => setOpen(false);
    const { systemId } = useParams();
    const [actors, isSuccessActors] = useSystemActors(systemId);
    const [selectedActor, setSelectedActor] = useState("");

    const { mutateAsync, isPending } = useMutation<
        InterfaceOutput,
        unknown,
        InterfaceInput
    >({
        mutationFn: async ({ name, description, actor }) => {
            const { data } = await authAxios.post(`v1/metadata/interfaces/`, {
                name: name,
                description: description,
                system_id: system,
                actor_id: actor,
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
            actor: `${formData.get("actor")}`,
        }).then(() => {
            queryClient.invalidateQueries({ queryKey: ["interfaces"] });
            close();
        });
    };

    if (isPending) {
        return (
            <Modal open>
                <ModalDialog>
                    <CircularProgress className="animate-spin" />
                </ModalDialog>
            </Modal>
        )
    };

    return (
        <Modal open={open} onClose={() => close()}>
            <ModalDialog>
                <div className="flex w-full flex-row justify-between pb-1">
                    <div className="flex flex-col">
                        <h1 className="font-bold">Create Interface</h1>
                        <h3 className="text-sm">Start a new interface</h3>
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
                    id="create-interface"
                    className="flex min-w-96 flex-col gap-2"
                    onSubmit={onSubmit}
                >
                    <FormControl required>
                        <FormLabel>Name</FormLabel>
                        <Input name="name" placeholder="Interface" required />
                    </FormControl>
                    <FormControl>
                        <FormLabel>Description</FormLabel>
                        <Input
                            name="description"
                            placeholder="A whole new world..."
                        />
                    </FormControl>
                    <FormControl required>
                        <FormLabel>Actor</FormLabel>
                        <Select
                            name="actor"
                            options={actors.map((e) => ({ label: e.data.name, value: e.id }))}
                            value={selectedActor}
                            onChange={setSelectedActor}
                            required
                        />
                    </FormControl>
                </form>
                <Divider />
                <div className="flex flex-row pt-1">
                    <Button form="create-interface" type="submit">
                        Create
                    </Button>
                </div>
            </ModalDialog>
        </Modal>
    );
};

export default CreateInterface;
