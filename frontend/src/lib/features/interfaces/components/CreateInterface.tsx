import { createInterfaceAtom } from "$browser/atoms";
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
import { useAtom } from "jotai";
import React, { useState } from "react";
import Select from "react-select";
import { useParams } from "react-router";
import { useSystemActors } from "$lib/features/interfaces/queries";
import { useCreateInterface } from "../../../../api/metadata/hooks/interface";
import type { InterfaceCreate } from "../../../../api/metadata/interface";

type Props = {
    system: string;
};

export const CreateInterface: React.FC<Props> = ({ system }) => {
    const [open, setOpen] = useAtom(createInterfaceAtom);
    const close = () => setOpen(false);
    const { systemId } = useParams();
    const [actors, isSuccessActors] = useSystemActors(systemId);
    const [selectedActor, setSelectedActor] = useState("");

    const { mutateAsync, isPending } = useCreateInterface();

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);

        // Styling fields are left out so the backend defaults are used
        mutateAsync({
            system_id: system,
            name: `${formData.get("name")}`,
            description: `${formData.get("description")}`,
            actor_id: `${formData.get("actor")}`,
        } as InterfaceCreate).then(() => {
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
                        <Select<{ label: string; value: string }>
                            name="actor"
                            options={actors
                                .filter((actor) => actor.id != null)
                                .map((actor) => ({
                                    label: actor.data.name,
                                    value: actor.id!,
                                }))}
                            value={
                                actors
                                    .filter((actor) => actor.id != null)
                                    .map((actor) => ({
                                        label: actor.data.name,
                                        value: actor.id!,
                                    }))
                                    .find((option) => option.value === selectedActor) ?? null
                            }
                            onChange={(option) => setSelectedActor(option?.value ?? "")}
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
