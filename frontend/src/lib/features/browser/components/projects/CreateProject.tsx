import { createProjectAtom } from "$browser/atoms";
import { createProject } from "$lib/endpoints/projects";
import type { ProjectCreate, ProjectOut } from "$lib/types/projects";
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
import React from "react";

export const CreateProject: React.FC = () => {
    const [open, setOpen] = useAtom(createProjectAtom);
    const close = () => setOpen(false);

    const { mutateAsync, isPending } = useMutation<
        ProjectOut,
        unknown,
        ProjectCreate
    >({
        mutationFn: createProject,
    });

    const onSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);

        mutateAsync({
            name: `${formData.get("name")}`,
            description: `${formData.get("description")}`,
        }).then(() => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
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
                        <h1 className="font-bold">Create Project</h1>
                        <h3 className="text-sm">Start a new project</h3>
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
                        <Input name="name" placeholder="Project" required />
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
                    <Button form="create-project" type="submit">
                        Create
                    </Button>
                </div>
            </ModalDialog>
        </Modal>
    );
};

export default CreateProject;
