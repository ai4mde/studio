import React, {useState, useEffect } from "react";
import { Modal, Button, Typography } from "@mui/joy";
import Editor from "@monaco-editor/react";

type CodeEditorModalProps = {
    open: boolean;
    onClose: () => void;
    onSave: (code: string) => void;
    initialCode?: string;
    classes?: string[];
}

const CodeEditorModal: React.FC<CodeEditorModalProps> = ({ open, onClose, onSave, initialCode, classes }) => {
    const [currentCode, setCurrentCode] = useState(initialCode);

    useEffect(() => {
        if (!initialCode && classes) {
            const generatedCode = `def custom_code(active_process: ActiveProcess) -> None:\n` +
                "    # The following variables are Django QuerySet objects related to the active process\n" +
                classes.map((cls) => `    ${cls.toLowerCase()}s = active_process.${cls.toLowerCase()}s # Do not change this line`).join("\n") +
                `\n    pass`;
            setCurrentCode(generatedCode);
        }
    }, [initialCode, classes]);

    const handleSave = () => {
        onSave(currentCode);
        onClose();
    };

    return (
        <Modal open={open} onClose={onClose}>
            <div style={{ padding: "16px", backgroundColor: "white", borderRadius: "8px", width: "800px", height: "650px", margin: "auto" }}>
                <Typography level="h2" component="h2" style={{ marginBottom: "16px" }}>
                    Edit Code
                </Typography>
                <div style={{ height: "500px", marginBottom: "16px" }}>
                    <Editor
                        height="100%"
                        defaultLanguage="python"
                        value={currentCode}
                        onChange={(value) => setCurrentCode(value || "")}
                        options={{
                            theme: "vs-light",
                            automaticLayout: true,
                        }}
                    />
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <Button variant="plain" onClick={onClose} style={{ marginRight: "8px" }}>
                        Cancel
                    </Button>
                    <Button variant="solid" onClick={handleSave}>
                        Save
                    </Button>
                </div>
            </div>
        </Modal>
    );
};

export default CodeEditorModal;
