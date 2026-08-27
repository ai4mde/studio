import { Step, StepIndicator, Stepper } from "@mui/joy";
import React from "react";

type Props = {
    step: number;
    variant?: "hitl" | "legacy";
};

export const Steps: React.FC<Props> = ({ step, variant = "legacy" }) => {
    const labels =
        variant === "hitl"
            ? [
                  "Select workflow",
                  "Enter process text",
                  "Generate candidates",
                  "Select candidate",
                  "Edit and refine",
              ]
            : [
                  "Select pipeline",
                  "Upload requirements",
                  "Select model",
                  "Run model",
                  "Add to diagram",
              ];
    return (
        <Stepper>
            <Step
                indicator={
                    <StepIndicator
                        variant={step > 0 ? "solid" : "outlined"}
                        color={
                            step > 0
                                ? step > 1
                                    ? "success"
                                    : "primary"
                                : "neutral"
                        }
                    >
                        1
                    </StepIndicator>
                }
            >
                {labels[0]}
            </Step>
            <Step
                indicator={
                    <StepIndicator
                        variant={step > 1 ? "solid" : "outlined"}
                        color={
                            step > 1
                                ? step > 2
                                    ? "success"
                                    : "primary"
                                : "neutral"
                        }
                    >
                        2
                    </StepIndicator>
                }
            >
                {labels[1]}
            </Step>
            <Step
                indicator={
                    <StepIndicator
                        variant={step > 2 ? "solid" : "outlined"}
                        color={
                            step > 2
                                ? step > 3
                                    ? "success"
                                    : "primary"
                                : "neutral"
                        }
                    >
                        3
                    </StepIndicator>
                }
            >
                {labels[2]}
            </Step>
            <Step
                indicator={
                    <StepIndicator
                        variant={step > 3 ? "solid" : "outlined"}
                        color={
                            step > 3
                                ? step > 4
                                    ? "success"
                                    : "primary"
                                : "neutral"
                        }
                    >
                        4
                    </StepIndicator>
                }
            >
                {labels[3]}
            </Step>
            <Step
                indicator={
                    <StepIndicator
                        variant={step > 4 ? "solid" : "outlined"}
                        color={
                            step > 4
                                ? step > 5
                                    ? "success"
                                    : "primary"
                                : "neutral"
                        }
                    >
                        5
                    </StepIndicator>
                }
            >
                {labels[4]}
            </Step>
        </Stepper>
    );
};
