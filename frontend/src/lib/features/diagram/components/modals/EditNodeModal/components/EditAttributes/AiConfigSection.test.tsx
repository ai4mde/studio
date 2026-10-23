import React, { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import AiConfigSection from "./AiConfigSection";
import { aiPresets, buildAiConfig, upgradeAiConfig, validateAiConfig } from "./aiPresets";

afterEach(cleanup);
const defaults = (index = 0) => {
    const preset = aiPresets[index];
    return buildAiConfig({ preset, className: preset.applicableTo.className,
        attributeName: preset.applicableTo.attributeName, modelProfile: preset.defaultModelProfile });
};
const previous = (index: number) => {
    const config: any = defaults(index);
    config.ai_config_version = "1.1";
    delete config.context.history.unit;
    config.context.history.max_scan_loans = config.context.history.max_scan_records;
    delete config.context.history.max_scan_records;
    if (index === 0) config.template.name = "library_late_risk_v2";
    return config;
};
describe("CFG-03 explicit preset reset", () => {
    for (const index of [0, 1]) {
        const preset = aiPresets[index];
        const mount = (config: any, update = vi.fn()) => ({update, view: render(<AiConfigSection
            className={preset.applicableTo.className} update={update}
            attribute={{name: preset.applicableTo.attributeName, type: "str", ai_config: config}} />)});
        it("resets valid 1.1 " + preset.id + " only on explicit action", () => {
            const config = previous(index); config.context.history.limit = 7;
            config.output.on_skip = "PENDING"; config.model_profile = index === 0 ? "strong" : "cheap";
            const saved = JSON.stringify(config);
            const {update} = mount(config);
            expect(update).not.toHaveBeenCalled();
            expect(screen.queryByLabelText("History limit")).toBeNull();
            fireEvent.click(screen.getByText("Reset to v1.2 preset"));
            expect(update.mock.calls[0][0].ai_config).toEqual(defaults(index));
            expect(JSON.stringify(config)).toBe(saved);
        });
        for (const version of ["1.0", "9.0", undefined]) {
            it("preserves unsupported version " + version + " " + preset.id, () => {
                const config = previous(index); config.ai_config_version = version;
                const saved = JSON.stringify(config); const {update} = mount(config);
                expect(screen.queryByText("Reset to v1.2 preset")).toBeNull();
                expect(screen.queryByLabelText("History limit")).toBeNull();
                expect(update).not.toHaveBeenCalled(); expect(JSON.stringify(config)).toBe(saved);
                expect(() => upgradeAiConfig(config, preset)).toThrow();
            });
        }
        it("rejects illegal previous values " + preset.id, () => {
            const config = previous(index);config.model_profile = "unknown";
            mount(config);
            expect(screen.getByRole("alert").textContent).toContain("model_profile");
            expect(screen.queryByText("Reset to v1.2 preset")).toBeNull();
            expect(() => upgradeAiConfig(config,preset)).toThrow();
        });
        it("does not edit invalid current content " + preset.id, () => {
            const config:any=defaults(index);config.context.history.limit=0;
            mount(config);expect(screen.queryByLabelText("History limit")).toBeNull();
        });
    }
});
describe("CFG-04 persisted path editing", () => {
    it("preserves edited and imported policy across profile changes and panel remount/export", () => {
        const initial: any = defaults();
        initial.context.history.order_by = "-loan_date";
        initial.context.history.max_scan_records = 333;
        initial.output.reason.max_length = 77;
        let saved: any;
        function Harness() {
            const [attribute, setAttribute] = useState({ name: "late_risk", type: "str", ai_config: initial });
            const [open, setOpen] = useState(true);
            saved = attribute;
            return <><button onClick={() => setOpen(!open)}>Toggle panel</button>
                {open && <AiConfigSection attribute={attribute} className="BookLoan" update={setAttribute} />}</>;
        }
        render(<Harness />);
        const edit = (label: string, value: string) => {
            const input = screen.getByLabelText(label);
            fireEvent.change(input, { target: { value } }); fireEvent.blur(input);
        };
        edit("History limit", "7");
        fireEvent.change(screen.getByLabelText("Model profile"), { target: { value: "strong" } });
        edit("Allowed values", "SAFE, RISKY");
        edit("On skip", "PENDING");
        fireEvent.click(screen.getByText("Toggle panel")); fireEvent.click(screen.getByText("Toggle panel"));
        const exported = JSON.parse(JSON.stringify(saved.ai_config));
        expect(exported.context.history).toEqual({ ...initial.context.history, limit: 7 });
        expect(exported.output).toEqual({ ...initial.output, allowed_values: ["SAFE", "RISKY"], on_skip: "PENDING" });
        expect(exported.model_profile).toBe("strong");
        expect(validateAiConfig(exported, aiPresets[0])).toBeUndefined();
        edit("History limit", "0");
        expect(saved.ai_config.context.history.limit).toBe(7);
        expect(screen.getByRole("alert").textContent).toContain("limit");
        edit("Allowed values", "SAFE,,RISKY");
        expect(saved.ai_config.output.allowed_values).toEqual(["SAFE", "RISKY"]);
    });
});
