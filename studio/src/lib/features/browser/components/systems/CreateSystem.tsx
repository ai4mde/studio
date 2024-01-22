import { createSystemAtom } from "$browser/atoms";
import { authAxios } from "$lib/features/auth/state/auth";
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
import React from "react";

type SystemInput = {
    name: string;
    description?: string;
};

type SystemOutput = {
    id: string;
    name: string;
    description: string;
};

type Props = {
    project: string;
};

export const CreateSystem: React.FC<Props> = ({ project }) => {
    const [open, setOpen] = useAtom(createSystemAtom);
    const close = () => setOpen(false);

    const { mutate, isLoading } = useMutation<
        SystemOutput,
        unknown,
        SystemInput
    >({
        mutationFn: async ({ name, description }) => {
            const { data } = await authAxios.post(`v1/metadata/systems/`, {
                name: name,
                description: description,
                project: project,
            });

            return data;
        },
    });

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);

        mutate({
            name: `${formData.get("name")}`,
            description: `${formData.get("description")}`,
        });
    };

    if (isLoading) {
        <Modal open>
            <ModalDialog>
                <CircularProgress className="animate-spin" />
            </ModalDialog>
        </Modal>;
    }

    return (
        <Modal open={open} onClose={() => close()}>
            <ModalDialog>
                <div className="flex flex-row w-full justify-between pb-1">
                    <div className="flex flex-col">
                        <h1 className="font-bold">Create System</h1>
                        <h3 className="text-sm">Start a new system</h3>
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
                    id="create-system"
                    className="flex flex-col min-w-96 gap-2"
                    onSubmit={onSubmit}
                >
                    <FormControl required>
                        <FormLabel>Name</FormLabel>
                        <Input name="name" placeholder="System" required />
                    </FormControl>
                    <FormControl>
                        <FormLabel>Description</FormLabel>
                        <Input
                            name="description"
                            placeholder="A whole new world..."
                        />
                    </FormControl>
                </form>
                <Divider />
                <div className="flex flex-row pt-1">
                    <Button form="create-system" type="submit">
                        Create
                    </Button>
                </div>
            </ModalDialog>
        </Modal>
    );
};

export default CreateSystem;
