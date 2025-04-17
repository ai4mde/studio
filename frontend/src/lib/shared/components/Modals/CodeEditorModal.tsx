import React from "react";
import { Modal, Button, Typography } from "@mui/joy";
import Editor from "@monaco-editor/react";

type CodeEditorModalProps = {
    open: boolean;
    onClose: () => void;
    onSave: (code: string) => void;
    initialCode: string;
}

const CodeEditorModal: React.FC<CodeEditorModalProps> = ({ open, onClose, onSave, initialCode }) => {
    const [currentCode, setCurrentCode] = React.useState(initialCode);

    const handleSave = () => {
        onSave(currentCode);
        onClose();
    };

    return (
        <Modal open={open} onClose={onClose}>
            <div style={{ padding: "16px", backgroundColor: "white", borderRadius: "8px", width: "600px", margin: "auto" }}>
                <Typography level="h2" component="h2" style={{ marginBottom: "16px" }}>
                    Edit Code
                </Typography>
                <div style={{ height: "400px", marginBottom: "16px" }}>
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
