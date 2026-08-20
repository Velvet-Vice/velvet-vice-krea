import { app } from "../../../scripts/app.js";

const NODE_CLASS = "VelvetViceKreaPromptDirector";

function ensureCss() {
    window.VelvetViceKreaDesign?.installCss?.();
}

function findWidget(node, name) {
    return node.widgets?.find((widget) => widget.name === name);
}

function firstValue(value, fallback = "") {
    if (Array.isArray(value)) {
        return value.length ? String(value[0] ?? fallback) : fallback;
    }
    return value == null ? fallback : String(value);
}

app.registerExtension({
    name: "VelvetVice.KREA.VisionPromptDirectorSurfaceV105",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_CLASS) return;

        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = originalCreated?.apply(this, arguments);
            ensureCss();

            this.title = "VELVET VICE KREA · VISION PROMPT DIRECTOR";

            const shell = document.createElement("div");
            shell.className = "vvk-shell";

            const head = document.createElement("div");
            head.className = "vvk-head";
            const brand = document.createElement("div");
            brand.className = "vvk-brand";
            brand.textContent = "VELVET VICE · KREA VISION PROMPTER";
            const badge = document.createElement("div");
            badge.className = "vvk-badge";
            badge.textContent = "READY";
            head.append(brand, badge);
            shell.appendChild(head);

            const body = document.createElement("div");
            body.className = "vvk-body";

            const chips = document.createElement("div");
            chips.className = "vvk-prompt-meta";
            const profileChip = document.createElement("div");
            profileChip.className = "vvk-chip";
            const modeChip = document.createElement("div");
            modeChip.className = "vvk-chip";
            const ollamaChip = document.createElement("div");
            ollamaChip.className = "vvk-chip";
            const freedomChip = document.createElement("div");
            freedomChip.className = "vvk-chip";
            chips.append(profileChip, modeChip, ollamaChip, freedomChip);

            const panel = document.createElement("div");
            panel.className = "vvk-panel";
            const label = document.createElement("div");
            label.className = "vvk-label";
            label.textContent = "FINAL PROMPT SENT TO KREA 2";
            const prompt = document.createElement("textarea");
            prompt.className = "vvk-textarea";
            prompt.readOnly = true;
            prompt.placeholder = "Run the workflow to display the selected final prompt.";
            prompt.style.minHeight = "142px";
            panel.append(label, prompt);

            const footer = document.createElement("div");
            footer.className = "vvk-foot";
            const statusWrap = document.createElement("div");
            statusWrap.style.display = "flex";
            statusWrap.style.alignItems = "center";
            statusWrap.style.gap = "8px";
            const dot = document.createElement("div");
            dot.className = "vvk-dot ok";
            const status = document.createElement("div");
            status.textContent = "Ready · Manual mode never contacts Ollama";
            statusWrap.append(dot, status);
            const counts = document.createElement("div");
            counts.textContent = "0 WORDS · 0 CHARACTERS";
            footer.append(statusWrap, counts);

            const actions = document.createElement("div");
            actions.style.display = "flex";
            actions.style.gap = "8px";
            actions.style.marginTop = "10px";
            const copy = document.createElement("button");
            copy.className = "vvk-button vvk-run";
            copy.textContent = "COPY FINAL PROMPT";
            copy.addEventListener("click", async () => {
                const text = String(prompt.value || "");
                if (!text) {
                    status.textContent = "Nothing to copy yet";
                    dot.className = "vvk-dot warn";
                    return;
                }
                try {
                    await navigator.clipboard.writeText(text);
                    status.textContent = "Copied to clipboard";
                    dot.className = "vvk-dot ok";
                } catch (error) {
                    status.textContent = `Copy failed: ${error?.message || error}`;
                    dot.className = "vvk-dot fail";
                }
            });
            actions.append(copy);

            body.append(chips, panel, footer, actions);
            shell.appendChild(body);

            const dom = this.addDOMWidget(
                "vv_krea_director_surface",
                "VELVET VICE KREA DIRECTOR",
                shell,
                { serialize: false, hideOnZoom: false }
            );
            dom.serialize = false;
            dom.serializeValue = () => undefined;
            dom.computeSize = (width) => [width, 350];

            this.vvKreaPrompt = prompt;
            this.vvKreaCounts = counts;
            this.vvKreaStatus = status;
            this.vvKreaStatusDot = dot;
            this.vvKreaBadge = badge;

            const refresh = () => {
                profileChip.textContent = `PROFILE · ${findWidget(this, "profile")?.value ?? "CREATE"}`;
                modeChip.textContent = `MODE · ${findWidget(this, "prompt_mode")?.value ?? "MANUAL"}`;
                const model = String(findWidget(this, "ollama_model")?.value ?? "OLLAMA");
                ollamaChip.textContent = `QWEN · ${model.split("/").pop().slice(0, 26)}`;
                freedomChip.textContent = `FREEDOM · ${findWidget(this, "director_freedom")?.value ?? "BALANCED"}`;
            };

            for (const name of ["profile", "prompt_mode", "ollama_model", "director_freedom"]) {
                const widget = findWidget(this, name);
                if (!widget) continue;
                const original = widget.callback;
                widget.callback = (value) => {
                    original?.call(widget, value);
                    refresh();
                };
            }
            refresh();
            this.setSize([
                Math.max(this.size?.[0] ?? 720, 720),
                Math.max(this.size?.[1] ?? 1120, 1120),
            ]);
            return result;
        };

        const originalExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            originalExecuted?.apply(this, arguments);
            const prompt = firstValue(message?.final_prompt);
            const words = firstValue(message?.word_count, "0");
            const characters = firstValue(message?.character_count, "0");
            const profile = firstValue(message?.profile, "CREATE");
            const runStatus = firstValue(message?.status, "Completed");

            if (this.vvKreaPrompt) this.vvKreaPrompt.value = prompt;
            if (this.vvKreaCounts) {
                this.vvKreaCounts.textContent = `${words} WORDS · ${characters} CHARACTERS`;
            }
            if (this.vvKreaStatus) this.vvKreaStatus.textContent = `${profile} · ${runStatus}`;
            if (this.vvKreaStatusDot) this.vvKreaStatusDot.className = "vvk-dot ok";
            if (this.vvKreaBadge) this.vvKreaBadge.textContent = "PROMPT READY";
            this.setDirtyCanvas?.(true, true);
        };
    },
});
