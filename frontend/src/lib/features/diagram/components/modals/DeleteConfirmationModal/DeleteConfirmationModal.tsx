import React from "react";
import { createPortal } from "react-dom";
import Draggable from "react-draggable";
import Button from "@mui/joy/Button";
import { X } from "lucide-react";
import style from "./deleteconfirmationmodal.module.css";

interface DeleteConfirmationModalProps {
    onConfirm: (deleteChildren: boolean) => void;
    onCancel: () => void;
}

export const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({ onConfirm, onCancel }) => {
    const nodeRef = React.useRef(null);

    return createPortal(
        <div className={style.modal}>
            <div className={style.wrapper}>
                <Draggable nodeRef={nodeRef}>
                    <div ref={nodeRef} className={style.main}>
                        <div className={style.head}>
                            <span className="p-2 px-3">Confirm Deletion</span>
                            <button className="m-1 mx-2 rounded-sm" onClick={onCancel}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className={style.body}>
                            <p>Do you want to delete the child nodes as well?</p>
                        </div>
                        <div className={style.actions}>
                            <Button color="danger" size="sm" onClick={() => onConfirm(true)}>
                                Yes
                            </Button>
                            <Button color="primary" size="sm" onClick={() => onConfirm(false)}>
                                No
                            </Button>
                            <Button color="neutral" size="sm" onClick={onCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                </Draggable>
            </div>
        </div>,
        document.body,
    );
};

export default DeleteConfirmationModal;