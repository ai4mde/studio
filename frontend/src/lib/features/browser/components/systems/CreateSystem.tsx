import { createSystemAtom } from "$browser/atoms";
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
import React from "react";
import { useCreateSystem } from "../../../../../api/metadata/hooks/system";

type Props = {
    project: string;
};

export const CreateSystem: React.FC<Props> = ({ project }) => {
    const [open, setOpen] = useAtom(createSystemAtom);
    const close = () => setOpen(false);
    const { mutateAsync, isPending } = useCreateSystem();

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();

        const formData = new FormData(e.currentTarget);

        mutateAsync({
            project_id: project,
            name: `${formData.get("name")}`,
            description: `${formData.get("description")}`,
        }).then(() => {
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
                    className="flex min-w-96 flex-col gap-2"
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
