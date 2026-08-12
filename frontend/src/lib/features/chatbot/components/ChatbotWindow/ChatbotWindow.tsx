import { chatbotOpenAtom } from "$chatbot/atoms";
import { authAxios } from "$lib/features/auth/state/auth";
import { runHitlOperation, useHitlOperation } from "$lib/features/ai/hitlOperation";
import { useDiagram } from "$lib/features/diagram/queries/diagram";
import { queryClient } from "$shared/hooks/queryClient";
import {
    Alert,
    Button,
    CircularProgress,
    IconButton,
    Input,
    Modal,
    ModalClose,
    ModalDialog,
    Textarea,
} from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { useAtom } from "jotai";
import React, { useEffect, useState } from "react";
import { SendHorizonal } from "lucide-react";
import { useMatch } from "react-router";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { wsURL } from "$lib/shared/globals";

export const ChatbotWindow: React.FC = () => {
    const [chatbotOpen, setChatbotOpen] = useAtom(chatbotOpenAtom);
    const close = () => setChatbotOpen(false);
    const diagramMatch = useMatch("/diagram/:diagramId");
    const diagramId = diagramMatch?.params?.diagramId;
    const { data: diagramData } = useDiagram(diagramId ?? "");
    const { sendMessage, lastJsonMessage, readyState } = useWebSocket(
        `${wsURL}/chat/changes/demo`,
    );
    const [messageHistory, setMessageHistory] = useState<any[]>([]);
    const [refinementStatus, setRefinementStatus] = useState<{
        tone: "success" | "danger";
        message: string;
    } | null>(null);
    const activeOperation = useHitlOperation((state) => state.activeOperation);

    const refineMutation = useMutation({
        mutationFn: async (instruction: string) => {
            await runHitlOperation("refinement", async () => {
                await authAxios.post("/v1/refine-model", {
                    system_id: diagramData?.system_id,
                    instruction,
                    pipeline_profile: "semantic_deterministic",
                });
            });
        },
        onSuccess: async () => {
            setRefinementStatus({
                tone: "success",
                message: "Diagram refined successfully.",
            });
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ["diagram", diagramId] }),
                queryClient.invalidateQueries({
                    queryKey: ["system-revisions", diagramData?.system_id],
                }),
                queryClient.invalidateQueries({
                    queryKey: ["system", `${diagramData?.system_id}`],
                }),
            ]);
        },
        onError: () => {
            setRefinementStatus({
                tone: "danger",
                message:
                    "We could not refine the diagram right now. Please try again.",
            });
        },
    });

    useEffect(() => {
        if (lastJsonMessage !== null) {
            setMessageHistory((prev) => prev.concat(lastJsonMessage));
        }
    }, [lastJsonMessage, setMessageHistory]);

    if (diagramId && diagramData?.system_id) {
        return (
            <Modal open={chatbotOpen} onClose={close} hideBackdrop>
                <ModalDialog>
                    <ModalClose />
                    <div className="flex w-[33vw] min-w-96 flex-col gap-4 p-4">
                        <div className="flex flex-col gap-1">
                            <h2 className="text-lg font-semibold">AI Refinement</h2>
                            <p className="text-sm text-stone-600">
                                Enter a short instruction to update the current
                                activity diagram.
                            </p>
                        </div>
                        <form
                            className="flex flex-col gap-3"
                            onSubmit={(event) => {
                                event.preventDefault();
                                const formData = new FormData(event.currentTarget);
                                const instruction = String(
                                    formData.get("instruction") ?? "",
                                ).trim();
                                if (!instruction) {
                                    return;
                                }
                                setRefinementStatus(null);
                                refineMutation.mutate(instruction);
                                event.currentTarget.reset();
                            }}
                        >
                            <Textarea
                                minRows={6}
                                name="instruction"
                                placeholder="Add a compliance review before approval."
                                required
                            />
                            <Button
                                type="submit"
                                disabled={activeOperation !== null}
                            >
                                {activeOperation === "refinement" ? (
                                    <CircularProgress size="sm" />
                                ) : (
                                    "Refine Diagram"
                                )}
                            </Button>
                        </form>
                        <div className="rounded-md bg-stone-50 p-3 text-sm text-stone-600">
                            Manual changes are saved automatically. Use Sync with AI
                            before refinement so the AI uses your latest diagram.
                        </div>
                        {refinementStatus ? (
                            <Alert
                                color={refinementStatus.tone}
                                variant="soft"
                            >
                                {refinementStatus.message}
                            </Alert>
                        ) : null}
                    </div>
                </ModalDialog>
            </Modal>
        );
    }

    return (
        <Modal open={chatbotOpen} onClose={close} hideBackdrop>
            <ModalDialog>
                <ModalClose />
                <div className="flex w-[33vw] min-w-96 flex-col gap-4 p-4">
                    <div className="flex h-96 flex-col items-center justify-start gap-2 overflow-y-scroll">
                        {readyState != ReadyState.OPEN && <CircularProgress />}
                        {messageHistory.map((message) => {
                            if (message.sent) {
                                return (
                                    <span className="w-[90%] place-self-end rounded-md bg-stone-200 p-2">
                                        {message.message}
                                    </span>
                                );
                            }
                            if (message.message) {
                                return (
                                    <span className="w-[90%] place-self-start rounded-md bg-blue-200 p-2">
                                        {message.message}
                                    </span>
                                );
                            }
                        })}
                    </div>
                    <form
                        onSubmit={(form) => {
                            form.preventDefault();
                            const formData = new FormData(form.currentTarget);
                            sendMessage(formData.get("message") as string);
                            setMessageHistory((prev) =>
                                prev.concat({
                                    sent: true,
                                    message: formData.get("message"),
                                }),
                            );
                            form.currentTarget.reset();
                        }}
                        className="flex flex-row gap-1"
                    >
                        <Input
                            type="text"
                            name="message"
                            size="sm"
                            fullWidth
                            required
                        />
                        <IconButton color="primary" variant="solid">
                            <SendHorizonal size={16} />
                        </IconButton>
                    </form>
                </div>
            </ModalDialog>
        </Modal>
    );
};
