import { useNewNodeModal } from "$diagram/stores/modals";
import { Command } from "cmdk";
import { PlusCircle, Workflow } from "lucide-react";
import React, { useEffect } from "react";
import style from "./commandmenu.module.css";

export const CommandMenu: React.FC = () => {
    const [open, setOpen] = React.useState(false);
    const newNodeModal = useNewNodeModal();

    // Toggle the menu when ⌘K is pressed
    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((open) => !open);
            }

            if (e.key === "Escape") {
                e.preventDefault();
                setOpen(false);
            }
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, []);

    return (
        <div
            className={style.vercel}
            style={{
                display: open ? "flex" : "none",
            }}
        >
            {open && (
                <>
                    <div
                        style={{
                            position: "fixed",
                            inset: 0,
                            zIndex: -1,
                        }}
                        onClick={() => setOpen(false)}
                    ></div>
                    <Command label="Global Command Menu">
                        <div className={style["cmdk-linear-badge"]}>
                            Diagram
                        </div>
                        <Command.Input
                            autoFocus
                            placeholder="Type a command or search..."
                        />
                        <Command.List>
                            <Command.Empty>No results found.</Command.Empty>

                            <Command.Group heading="Nodes">
                                <Command.Item
                                    onSelect={() => {
                                        newNodeModal.open();
                                        setOpen(false);
                                    }}
                                >
                                    New
                                    <PlusCircle size={32} />
                                </Command.Item>
                            </Command.Group>

                            <Command.Group heading="Connections">
                                <Command.Item
                                    onSelect={() => {
                                        // newNodeModal.open()
                                        // setOpen(false)
                                    }}
                                >
                                    Connect
                                    <Workflow size={32} />
                                </Command.Item>
                            </Command.Group>
                        </Command.List>
                    </Command>
                </>
            )}
        </div>
    );
};

export default CommandMenu;
