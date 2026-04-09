import React from "react";
import { Modal, ModalClose, ModalDialog, Divider, Button } from "@mui/joy";
import FileUpload from "$shared/components/ui/FileUpload";

type UploadFileModalProps = {
  open: boolean;
  onClose: () => void;
  file: File | null;
  onFileChange: (file: File | null) => void;
  onConfirm: () => void;
  isUploading?: boolean;
  accept?: string;
  title?: string;
  description?: string;
  label?: string;
  error?: string | null;
};

const UploadFileModal: React.FC<UploadFileModalProps> = ({
  open,
  onClose,
  file,
  onFileChange,
  onConfirm,
  isUploading = false,
  error = null,
  accept = "application/json,.json",
  title = "Upload file",
  description = "Select a file to upload.",
  label = "Upload file",
}) => {
  return (
    <Modal open={open} onClose={onClose}>
      <ModalDialog
        sx={{
          width: 360,
          maxWidth: "90vw",
        }}
      >
        <div className="flex w-full flex-row justify-between pb-1">
          <div className="flex flex-col">
            <h1 className="font-bold">{title}</h1>
            <h3 className="text-sm">{description}</h3>
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

        <div className="pt-2">
          <FileUpload
            accept={accept}
            file={file}
            onFileChange={onFileChange}
            disabled={isUploading}
            label={label}
          />
        </div>
        {error && (
          <p className="pt-2 text-sm text-red-500 break-words whitespace-pre-wrap">
            {error}
          </p>
        )}
        <div className="flex flex-row justify-end gap-3 pt-2">
          <Button
            variant="outlined"
            color="neutral"
            onClick={onClose}
            disabled={isUploading}
          >
            Cancel
          </Button>

          <Button
            variant="solid"
            onClick={onConfirm}
            disabled={!file || isUploading}
            loading={isUploading}
          >
            Upload
          </Button>
        </div>
      </ModalDialog>
    </Modal>
  );
};

export default UploadFileModal;