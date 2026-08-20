import { app } from "../../../scripts/app.js";

const NODE_CLASS = "VelvetViceKreaStageRunner";
const BYPASS_MODE = 4;

const TARGETS = Object.freeze({
    BASE: ["CREATE — BASE PREVIEW • FIRST SAMPLER"],
    REFINEMENT: ["CREATE — REFINEMENT PREVIEW • SECOND SAMPLER"],
    SEEDVR2: ["CREATE — FINAL PREVIEW"],
});

const DETAILER_TARGETS = Object.freeze([
    "FEMALE BREAST DETAILER REVIEW PREVIEW",
    "VAGINA DETAILER REVIEW PREVIEW",
    "PENIS DETAILER REVIEW PREVIEW",
    "HAND DETAILER REVIEW PREVIEW",
    "FACE DETAILER PREVIEW",
]);

function ensureCss() {
    window.VelvetViceKreaDesign?.installCss?.();
}

function allNodes() {
    return app.graph?._nodes ?? [];
}

function isActive(node) {
    return Boolean(node) && Number(node.mode ?? 0) !== BYPASS_MODE;
}

function byTitle(title) {
    return allNodes().find((node) => String(node?.title ?? "") === title) ?? null;
}

function resolveTarget(stage) {
    if (stage === "DETAILER") {
        for (const title of DETAILER_TARGETS) {
            const node = byTitle(title);
            if (isActive(node)) return node;
        }
        return null;
    }
    for (const title of TARGETS[stage] ?? []) {
        const node = byTitle(title);
        if (isActive(node)) return node;
    }
    return null;
}

function labelFor(stage) {
    if (stage === "REFINEMENT") return "REFINEMENT";
    if (stage === "SEEDVR2") return "SEEDVR2 / FINAL";
    return stage;
}

async function queueStage(stage, ui) {
    const target = resolveTarget(stage);
    if (!target) {
        ui.status.textContent = stage === "DETAILER"
            ? "No enabled detailer found. Enable a detailer group first."
            : `Stage ${labelFor(stage)} is bypassed or unavailable in the current mode.`;
        ui.dot.className = "vvk-dot warn";
        return;
    }

    ui.status.textContent = `Queuing ${labelFor(stage)} → ${target.title}`;
    ui.dot.className = "vvk-dot ok";
    try {
        // Same queueNodeIds path used by ComfyUI's Queue Selected Output Nodes
        // command for partial execution. These targets are existing PreviewImage
        // output nodes in the root graph, so no render-path rewiring is needed.
        await app.queuePrompt(0, 1, { queueNodeIds: [String(target.id)] });
        ui.status.textContent = `${labelFor(stage)} queued as partial execution`;
        ui.dot.className = "vvk-dot ok";
    } catch (error) {
        ui.status.textContent = `Partial execution failed: ${error?.message || error}`;
        ui.dot.className = "vvk-dot fail";
    }
}

app.registerExtension({
    name: "VelvetVice.KREA.RenderThisStageV104",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_CLASS) return;

        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalCreated?.apply(this, arguments);
            ensureCss();
            this.title = "VELVET VICE · RENDER THIS STAGE";

            const shell = document.createElement("div");
            shell.className = "vvk-shell";

            const head = document.createElement("div");
            head.className = "vvk-head";
            const brand = document.createElement("div");
            brand.className = "vvk-brand";
            brand.textContent = "VELVET VICE · RENDER THIS STAGE";
            const badge = document.createElement("div");
            badge.className = "vvk-badge";
            badge.textContent = "PARTIAL";
            head.append(brand, badge);
            shell.appendChild(head);

            const body = document.createElement("div");
            body.className = "vvk-body";
            const hint = document.createElement("div");
            hint.className = "vvk-label";
            hint.textContent = "CREATE STAGE · EXECUTES ONLY THE REQUIRED UPSTREAM PATH";

            const grid = document.createElement("div");
            grid.className = "vvk-grid";
            const ui = {};
            for (const stage of ["BASE", "REFINEMENT", "DETAILER", "SEEDVR2"]) {
                const button = document.createElement("button");
                button.className = "vvk-button";
                button.textContent = `▶ ${labelFor(stage)}`;
                button.title = `Partial execute up to the ${labelFor(stage)} output`;
                button.addEventListener("click", () => queueStage(stage, ui));
                grid.appendChild(button);
            }

            const footer = document.createElement("div");
            footer.className = "vvk-foot";
            const statusWrap = document.createElement("div");
            statusWrap.style.display = "flex";
            statusWrap.style.alignItems = "center";
            statusWrap.style.gap = "8px";
            const dot = document.createElement("div");
            dot.className = "vvk-dot ok";
            const status = document.createElement("div");
            status.textContent = "Ready · uses ComfyUI partial execution · full workflow remains unchanged";
            statusWrap.append(dot, status);
            footer.append(statusWrap);

            ui.status = status;
            ui.dot = dot;
            body.append(hint, grid, footer);
            shell.appendChild(body);

            const dom = this.addDOMWidget(
                "vv_krea_stage_runner_surface",
                "VELVET VICE KREA STAGE RUNNER",
                shell,
                { serialize: false, hideOnZoom: false }
            );
            dom.serialize = false;
            dom.serializeValue = () => undefined;
            dom.computeSize = (width) => [width, 145];

            this.setSize([
                Math.max(this.size?.[0] ?? 820, 820),
                Math.max(this.size?.[1] ?? 180, 180),
            ]);
            return result;
        };
    },
});
