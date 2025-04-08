import { Step, StepIndicator, Stepper } from "@mui/joy";
import React from "react";

type Props = {
    step: number;
};

export const Steps: React.FC<Props> = ({ step }) => {
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
                Select pipeline
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
                Upload requirements
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
                Select model
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
                Run model
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
                Add to diagram
            </Step>
        </Stepper>
    );
};
