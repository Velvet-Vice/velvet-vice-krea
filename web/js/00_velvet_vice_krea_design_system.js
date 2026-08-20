import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const VERSION = "1.1.3";
const MARKER = "vvk_design_system";
const STYLE_ID = "vv-krea-design-system-v113";
const PALETTE = Object.freeze({
    emerald: "#00b386",
    emeraldSoft: "#7dffd9",
    violet: "#9b5cff",
    violetSoft: "#c8a3ff",
    body: "#0f1a17",
    bodyRaised: "#15231f",
    bodyDeep: "#0a0f0d",
    border: "rgba(0,255,194,.34)",
    borderSoft: "rgba(155,92,255,.15)",
    text: "#eaf8f1",
    muted: "#93b8a8",
    accent: "#9b5cff",
    ok: "#21c68b",
    warn: "#c89a55",
    fail: "#d95a72",
});

// Nodes with a complete DOM surface already draw their own Velvet Vice header.
// They must not also receive the canvas header or the native LiteGraph title.
const FULL_PANEL_TYPES = new Set([
    "VelvetViceKreaPromptDirector",
    "VelvetViceKreaStageRunner",
]);

const AUTO_ADOPT_TYPES = new Set([
    "Power Lora Loader (rgthree)",
]);

const themedNodes = new Set();
let activeNode = null;
let listenersInstalled = false;
let animationTimer = null;

function roundRect(ctx, x, y, w, h, r) {
    const radius = Math.max(0, Math.min(r, Math.abs(w) / 2, Math.abs(h) / 2));
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.arcTo(x + w, y, x + w, y + h, radius);
    ctx.arcTo(x + w, y + h, x, y + h, radius);
    ctx.arcTo(x, y + h, x, y, radius);
    ctx.arcTo(x, y, x + w, y, radius);
    ctx.closePath();
}

function nodeType(node) {
    return String(node?.comfyClass ?? node?.type ?? "");
}

function marked(node) {
    const props = node?.properties ?? {};
    return Boolean(
        nodeType(node).startsWith("VelvetViceKrea") ||
        props[MARKER] === true ||
        props[MARKER] === "KREA" ||
        props.vvk_design === true ||
        props.vvk_role ||
        props.vvk_badge
    );
}

function graphIsKrea() {
    return Boolean((app.graph?._nodes ?? []).some((node) => marked(node)));
}

function autoAdoptable(node) {
    return AUTO_ADOPT_TYPES.has(nodeType(node));
}

function graphHasKreaAnchor() {
    return Boolean((app.graph?._nodes ?? []).some((node) => marked(node) && !autoAdoptable(node)));
}

function claimKreaThemeOwnership(node) {
    if (!node || !autoAdoptable(node) || !graphHasKreaAnchor()) return false;
    const props = node.properties ?? (node.properties = {});
    props[MARKER] = "KREA";
    if (!props.vvk_role) props.vvk_role = "LOAD";
    if (!props.vvk_badge) props.vvk_badge = "LOAD";
    return true;
}

function adoptNewKreaNodes() {
    if (!graphIsKrea()) return;
    for (const node of app.graph?._nodes ?? []) {
        if (claimKreaThemeOwnership(node)) applyTheme(node);
    }
}

function pruneThemedNodes() {
    const live = new Set(app.graph?._nodes ?? []);
    for (const node of [...themedNodes]) {
        if (!live.has(node) || !marked(node)) themedNodes.delete(node);
    }
    if (activeNode && (!live.has(activeNode) || !marked(activeNode))) activeNode = null;
}

function decorative(node) {
    const type = nodeType(node).toLowerCase();
    return type.includes("label") || type.includes("note") || type.includes("bookmark") || type.includes("reroute");
}

function fullPanel(node) {
    return FULL_PANEL_TYPES.has(nodeType(node));
}

function noteLike(node) {
    const type = nodeType(node).toLowerCase();
    return type.includes("note");
}

function chromeExcluded(node) {
    const type = nodeType(node).toLowerCase();
    return fullPanel(node) || type.includes("label") || type.includes("bookmark") || type.includes("reroute") || type.includes("note");
}

function suppressNativeTitle(node) {
    if (!node || decorative(node) || node.__vvNativeTitleSuppressedV100) return;
    node.__vvNativeTitleSuppressedV100 = true;
    node.__vvDisplayTitle = String(node.title ?? nodeType(node) ?? "VELVET VICE");
    const originalGetTitle = typeof node.getTitle === "function" ? node.getTitle.bind(node) : null;
    node.__vvOriginalGetTitleV100 = originalGetTitle;
    // A zero-width title prevents LiteGraph from falling back to the class title.
    node.getTitle = function() { return "​"; };
    node.title_text_color = "rgba(0,0,0,0)";
    try {
        if (fullPanel(node) && globalThis.LiteGraph?.NO_TITLE != null) {
            node.title_mode = globalThis.LiteGraph.NO_TITLE;
        }
    } catch (_) {}
}

function badgeFor(node) {
    const props = node?.properties ?? {};
    if (props.vvk_badge) return String(props.vvk_badge).toUpperCase().slice(0, 18);
    const type = nodeType(node).toLowerCase();
    const title = String(node?.title ?? "").toLowerCase();
    if (type.includes("velvetvicecontrol")) return "CONTROL";
    if (type.includes("preflight") || title.includes("preflight")) return "CHECK";
    if (type.includes("output") || title.includes("output")) return "OUTPUT";
    if (title.includes("director")) return "DIRECT";
    if (title.includes("lora")) return "LORA";
    if (title.includes("model") || title.includes("vae")) return "LOAD";
    if (title.includes("pass") || title.includes("core") || title.includes("sampler")) return "ENGINE";
    if (title.includes("quality") || title.includes("scale") || title.includes("rife")) return "QUALITY";
    if (title.includes("memory") || title.includes("checkpoint")) return "MEMORY";
    if (title.includes("watermark") || title.includes("finish")) return "FINISH";
    if (title.includes("system") || title.includes("diagnostic")) return "SYSTEM";
    return "KREA";
}

function installCss() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .vvk-shell{
        --vvk-emerald:#00b386;--vvk-emerald-soft:#7dffd9;--vvk-violet:#9b5cff;--vvk-violet-soft:#c8a3ff;
        --vvk-body:#0f1a17;--vvk-raised:#15231f;--vvk-deep:#0a0f0d;
        --vvk-text:#eaf8f1;--vvk-muted:#93b8a8;--vvk-accent:#9b5cff;
      }
      @keyframes vvkGlow{0%,100%{filter:drop-shadow(0 0 4px rgba(0,255,194,.18))}50%{filter:drop-shadow(0 0 11px rgba(155,92,255,.43))}}
      @keyframes vvkSweep{0%{background-position:0% 50%}100%{background-position:200% 50%}}
      .vvk-shell{box-sizing:border-box;width:100%;font-family:Inter,"Segoe UI",Arial,sans-serif;color:var(--vvk-text);background:linear-gradient(145deg,#0a0f0d,#15231f);border:1px solid rgba(0,255,194,.24);border-radius:13px;overflow:hidden;box-shadow:0 10px 28px rgba(0,0,0,.27),inset 0 1px 0 rgba(255,255,255,.035)}
      .vvk-shell *{box-sizing:border-box}.vvk-head{position:relative;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 14px;background:linear-gradient(112deg,rgba(0,179,134,.88),rgba(106,27,255,.58));border-bottom:1px solid rgba(255,255,255,.085)}
      .vvk-head:after{content:"";position:absolute;left:0;right:0;bottom:0;height:2px;background:linear-gradient(90deg,rgba(125,255,217,.78),rgba(155,92,255,.74),transparent)}
      .vvk-brand{font-weight:850;letter-spacing:.115em;font-size:11px;color:#effff9;text-shadow:0 1px 10px rgba(0,0,0,.28)}
      .vvk-badge{white-space:nowrap;font-size:9px;font-weight:850;letter-spacing:.09em;padding:5px 8px;border-radius:999px;background:rgba(17,24,32,.72);color:#d9c9ff;border:1px solid rgba(200,163,255,.24);box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
      .vvk-body{padding:12px}.vvk-label{font-size:9px;font-weight:850;letter-spacing:.12em;text-transform:uppercase;color:#93b8a8;margin:0 0 7px}
      .vvk-panel{background:linear-gradient(145deg,rgba(21,35,31,.96),rgba(10,15,13,.96));border:1px solid rgba(0,255,194,.10);border-radius:10px;padding:10px;box-shadow:inset 0 1px 0 rgba(255,255,255,.025)}
      .vvk-segments{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:6px;margin-bottom:12px}.vvk-segment,.vvk-button{appearance:none;border:1px solid rgba(155,92,255,.16);background:linear-gradient(145deg,#172721,#111b18);color:#c8ded5;border-radius:9px;padding:9px 8px;font-weight:750;font-size:10px;cursor:pointer;transition:.14s ease}.vvk-segment:hover,.vvk-button:hover{border-color:rgba(155,92,255,.48);transform:translateY(-1px);box-shadow:0 5px 12px rgba(0,0,0,.18)}.vvk-segment.active{background:linear-gradient(135deg,#00a87f,#6a1bff);color:#fff;border-color:rgba(200,163,255,.42);box-shadow:inset 0 1px 0 rgba(255,255,255,.08)}
      .vvk-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.vvk-toggle{display:flex;align-items:center;justify-content:space-between;gap:10px;background:#15231f;border:1px solid rgba(255,255,255,.055);border-radius:9px;padding:10px 11px}.vvk-toggle span{font-size:10px;font-weight:750;color:#dcefe7}.vvk-switch{width:36px;height:20px;border-radius:999px;background:#263a33;border:1px solid rgba(255,255,255,.07);padding:2px;cursor:pointer;transition:.15s}.vvk-switch::after{content:"";display:block;width:14px;height:14px;border-radius:50%;background:#9db9ae;transition:.15s}.vvk-switch.on{background:linear-gradient(90deg,#00b386,#6a1bff)}.vvk-switch.on::after{transform:translateX(16px);background:#effff9}
      .vvk-input,.vvk-textarea{box-sizing:border-box;width:100%;background:#0a1310;border:1px solid rgba(155,92,255,.16);color:#eaf8f1;border-radius:8px;padding:10px 11px;outline:none}.vvk-textarea{resize:vertical;min-height:150px;line-height:1.42}.vvk-input:focus,.vvk-textarea:focus{border-color:rgba(155,92,255,.58);box-shadow:0 0 0 3px rgba(155,92,255,.13)}
      .vvk-foot{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:10px;font-size:9px;color:#8eaa9f}.vvk-dot{width:8px;height:8px;border-radius:50%;background:#78958a;box-shadow:0 0 0 3px rgba(0,179,134,.11)}.vvk-dot.ok{background:#21c68b}.vvk-dot.warn{background:#c89a55}.vvk-dot.fail{background:#d95a72}
      .vvk-checks{display:flex;flex-direction:column;gap:6px;max-height:342px;overflow:auto;padding-right:2px}.vvk-check{display:grid;grid-template-columns:11px 126px 1fr;gap:8px;align-items:start;background:#101c18;border:1px solid rgba(255,255,255,.045);border-radius:8px;padding:7px 8px;font-size:9px}.vvk-check strong{color:#dcefe7}.vvk-check em{font-style:normal;color:#8da99e;overflow-wrap:anywhere}.vvk-run{width:100%;margin:10px 0 8px;background:linear-gradient(135deg,#00b386,#6a1bff);border-color:rgba(200,163,255,.28);color:white}
      .vvk-stage-row{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin:10px 0}.vvk-stage{height:7px;border-radius:999px;background:#1d302a;transition:.15s}.vvk-stage.done{background:#00a77d}.vvk-stage.active{background:#9b5cff;box-shadow:0 0 10px rgba(155,92,255,.34)}.vvk-stage.error{background:#d95a72}.vvk-status{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.vvk-status-title{font-size:12px;font-weight:850;letter-spacing:.055em;color:#effff9}.vvk-status-detail{font-size:9px;color:#91ada2;margin-top:4px}.vvk-progress-track{height:7px;border-radius:999px;background:#0a0f0d;overflow:hidden;margin-top:10px}.vvk-progress{height:100%;width:0;background:linear-gradient(90deg,#00ffc2,#9b5cff);transition:width .12s linear}
      .vvk-video-frame{display:none;margin:12px auto 0;border-radius:10px;background:#070a0e;overflow:hidden;align-items:center;justify-content:center;border:1px solid rgba(155,92,255,.20);box-sizing:border-box;box-shadow:0 8px 20px rgba(0,0,0,.24);max-width:100%}.vvk-video-frame.visible{display:flex}.vvk-video-frame.portrait{box-shadow:0 9px 26px rgba(0,0,0,.31),0 0 0 1px rgba(155,92,255,.10)}.vvk-video{display:block;width:100%;height:100%;object-fit:contain;background:#070a0e}.vvk-video-meta{margin-top:7px;text-align:center;color:#8fa99f;font-size:9px;letter-spacing:.045em}.vvk-empty{margin-top:10px;padding:18px 10px;text-align:center;border-radius:9px;border:1px dashed rgba(155,92,255,.16);color:#7f9d91;font-size:10px;background:#0c1512}.vvk-advanced{margin-top:10px;border-top:1px solid rgba(255,255,255,.06);padding-top:9px}.vvk-advanced summary{cursor:pointer;color:#a6c1b6;font-size:9px;font-weight:750}.vvk-advanced-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;margin-top:8px}.vvk-mini{width:100%;box-sizing:border-box;background:#0a1310;color:#dcefe7;border:1px solid rgba(255,255,255,.075);border-radius:7px;padding:7px;font-size:9px}
      .vvk-prompt-meta{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:8px}.vvk-chip{font-size:9px;font-weight:800;letter-spacing:.06em;padding:5px 7px;border-radius:999px;background:#172d27;color:#cae2d8;border:1px solid rgba(255,255,255,.06)}
    `;
    document.head.appendChild(style);
}

function drawBody(ctx, node, width, height, titleHeight) {
    if (height <= titleHeight + 2) return;
    const grad = ctx.createLinearGradient(0, titleHeight, width, height);
    grad.addColorStop(0, "rgba(21,35,31,.98)");
    grad.addColorStop(.55, "rgba(15,26,23,.98)");
    grad.addColorStop(1, "rgba(10,15,13,.98)");
    ctx.fillStyle = grad;
    roundRect(ctx, 1.2, titleHeight - 1, width - 2.4, height - titleHeight, 9);
    ctx.fill();

    const sheen = ctx.createLinearGradient(0, titleHeight, width, titleHeight);
    sheen.addColorStop(0, "rgba(0,255,194,.11)");
    sheen.addColorStop(.5, "rgba(155,92,255,.08)");
    sheen.addColorStop(1, "rgba(155,92,255,0)");
    ctx.fillStyle = sheen;
    ctx.fillRect(8, titleHeight + 2, Math.max(0, width - 16), 1);

    // Subtle card lanes behind normal widget rows. This keeps native widgets usable
    // while giving them the same raised-panel language as the custom DOM modules.
    if (!decorative(node)) {
        for (const item of node.widgets ?? []) {
            if (item?.hidden || item?.__vvHidden || !Number.isFinite(item?.last_y)) continue;
            const y = Number(item.last_y) - 2;
            if (y < titleHeight + 2 || y > height - 10) continue;
            let h = 22;
            try {
                const measured = item.computeSize?.(Math.max(80, width - 20));
                if (Array.isArray(measured) && Number.isFinite(measured[1])) h = Math.max(20, Math.min(120, measured[1] + 2));
            } catch (_) {}
            ctx.fillStyle = "rgba(20,43,36,.30)";
            ctx.strokeStyle = "rgba(125,255,217,.055)";
            ctx.lineWidth = .7;
            roundRect(ctx, 8, y, Math.max(30, width - 16), Math.min(h, height - y - 5), 7);
            ctx.fill();
            ctx.stroke();
        }
    }
}

function drawHeader(ctx, node, width, titleHeight) {
    const state = node.__vvExecutionState ?? "idle";
    const active = state === "active";
    const error = state === "error";
    const phase = (Date.now() % 1600) / 1600;

    const grad = ctx.createLinearGradient(0, 0, width, titleHeight);
    grad.addColorStop(0, active ? "rgba(0,198,148,.96)" : "rgba(0,137,105,.96)");
    grad.addColorStop(.62, active ? "rgba(113,57,180,.92)" : "rgba(75,42,117,.90)");
    grad.addColorStop(1, "rgba(13,23,20,.98)");
    ctx.fillStyle = grad;
    roundRect(ctx, 1.2, 1.2, width - 2.4, titleHeight, 9);
    ctx.fill();
    ctx.fillRect(1.2, titleHeight - 8, width - 2.4, 8);

    const accent = ctx.createLinearGradient(0, 0, width, 0);
    accent.addColorStop(0, error ? "rgba(217,90,114,.90)" : "rgba(125,255,217,.82)");
    accent.addColorStop(.56, active ? "rgba(155,92,255,.88)" : "rgba(155,92,255,.66)");
    accent.addColorStop(1, "rgba(155,92,255,0)");
    ctx.fillStyle = accent;
    ctx.fillRect(8, titleHeight - 2, Math.max(0, width - 16), 2);

    if (active) {
        const sweep = ctx.createLinearGradient(-width + phase * width * 2, 0, phase * width * 2, 0);
        sweep.addColorStop(.35, "rgba(255,255,255,0)");
        sweep.addColorStop(.5, "rgba(225,210,255,.18)");
        sweep.addColorStop(.65, "rgba(255,255,255,0)");
        ctx.fillStyle = sweep;
        ctx.fillRect(1, 1, width - 2, titleHeight - 2);
    }

    const dotColor = error ? PALETTE.fail : active ? PALETTE.accent : state === "done" ? PALETTE.ok : "#78958a";
    ctx.fillStyle = "rgba(15,21,28,.68)";
    ctx.beginPath();
    ctx.arc(13, titleHeight / 2, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = dotColor;
    ctx.beginPath();
    ctx.arc(13, titleHeight / 2, active ? 3.4 + Math.sin(phase * Math.PI * 2) * .6 : 3.2, 0, Math.PI * 2);
    ctx.fill();

    const badge = badgeFor(node);
    ctx.font = "700 8px Inter, Segoe UI, Arial";
    const badgeWidth = width > 150 ? Math.min(92, ctx.measureText(badge).width + 15) : 0;
    if (badgeWidth) {
        const x = width - badgeWidth - 9;
        const y = 7;
        ctx.fillStyle = "rgba(15,22,29,.7)";
        roundRect(ctx, x, y, badgeWidth, 16, 8);
        ctx.fill();
        ctx.strokeStyle = "rgba(200,163,255,.20)";
        ctx.lineWidth = .8;
        ctx.stroke();
        ctx.fillStyle = "rgba(225,210,255,.92)";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(badge, x + badgeWidth / 2, y + 8.5, badgeWidth - 7);
    }

    const title = String(node.__vvDisplayTitle ?? node.title ?? nodeType(node) ?? "VELVET VICE");
    ctx.font = "700 12px Inter, Segoe UI, Arial";
    ctx.fillStyle = PALETTE.text;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    const maxTitle = Math.max(40, width - 34 - badgeWidth);
    ctx.fillText(title, 25, titleHeight / 2 + .5, maxTitle);
}

function applyTheme(node) {
    if (!node || !marked(node) || node.__vvSignatureThemeV113) return;
    node.__vvSignatureThemeV113 = true;
    node.__vvExecutionState = node.__vvExecutionState ?? "idle";
    themedNodes.add(node);

    node.color = PALETTE.emerald;
    node.bgcolor = PALETTE.body;
    node.boxcolor = PALETTE.accent;
    const customChrome = !chromeExcluded(node);
    suppressNativeTitle(node);
    try {
        if (globalThis.LiteGraph?.ROUND_SHAPE != null) node.shape = globalThis.LiteGraph.ROUND_SHAPE;
    } catch (_) {}

    const originalBackground = node.onDrawBackground;
    node.onDrawBackground = function(ctx) {
        originalBackground?.apply(this, arguments);
        if (!marked(this) || chromeExcluded(this)) return;
        const width = Number(this.size?.[0] ?? 0);
        const height = Number(this.size?.[1] ?? 0);
        if (width < 40 || height < 20) return;
        const titleHeight = 30;
        ctx.save();
        drawBody(ctx, this, width, height, titleHeight);
        ctx.restore();
    };

    const originalForeground = node.onDrawForeground;
    node.onDrawForeground = function(ctx) {
        originalForeground?.apply(this, arguments);
        if (!marked(this)) return;
        const width = Number(this.size?.[0] ?? 0);
        const height = Number(this.size?.[1] ?? 0);
        if (width < 40 || height < 20) return;
        const titleHeight = 30;
        ctx.save();
        if (!chromeExcluded(this)) drawHeader(ctx, this, width, titleHeight);

        const state = this.__vvExecutionState ?? "idle";
        ctx.lineWidth = state === "active" ? 2.1 : 1.1;
        ctx.strokeStyle = state === "error" ? "rgba(217,90,114,.78)" : state === "active" ? "rgba(155,92,255,.82)" : PALETTE.border;
        if (state === "active") {
            ctx.shadowColor = "rgba(155,92,255,.48)";
            ctx.shadowBlur = 12;
        }
        roundRect(ctx, .8, .8, width - 1.6, height - 1.6, 9);
        ctx.stroke();

        if (!chromeExcluded(this)) {
            ctx.fillStyle = state === "active" ? "rgba(0,255,194,.60)" : "rgba(0,179,134,.34)";
            roundRect(ctx, 4.5, titleHeight + 7, 3, Math.max(10, height - titleHeight - 14), 2);
            ctx.fill();
        }
        ctx.restore();
    };
    node.setDirtyCanvas?.(true, true);
}

function resolveNode(id) {
    if (id == null) return null;
    const raw = String(id);
    const top = Number(raw.split(":")[0]);
    return app.graph?.getNodeById?.(top) ?? app.graph?._nodes?.find((n) => String(n.id) === raw) ?? null;
}

function setState(node, state) {
    if (!node || !marked(node)) return;
    applyTheme(node);
    node.__vvExecutionState = state;
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas?.(true, true);
}

function resetStates(state = "idle") {
    pruneThemedNodes();
    if (!graphIsKrea()) return;
    for (const node of themedNodes) setState(node, state);
}

function activateNode(id) {
    pruneThemedNodes();
    const next = resolveNode(id);
    if (!marked(next)) {
        if (activeNode && activeNode.__vvExecutionState === "active") setState(activeNode, "done");
        activeNode = null;
        return;
    }
    if (activeNode && activeNode !== next && activeNode.__vvExecutionState === "active") setState(activeNode, "done");
    activeNode = next;
    setState(next, "active");
}

function installExecutionStyling() {
    if (listenersInstalled) return;
    listenersInstalled = true;
    api.addEventListener("execution_start", () => {
        pruneThemedNodes();
        activeNode = null;
        if (graphIsKrea()) resetStates("idle");
    });
    api.addEventListener("executing", ({ detail }) => {
        const id = detail?.node ?? detail;
        if (id == null) {
            if (activeNode) setState(activeNode, "done");
            activeNode = null;
            return;
        }
        activateNode(id);
    });
    api.addEventListener("progress", ({ detail }) => activateNode(detail?.node));
    api.addEventListener("executed", ({ detail }) => {
        const node = resolveNode(detail?.node);
        if (node) setState(node, "done");
    });
    api.addEventListener("execution_error", ({ detail }) => {
        const node = resolveNode(detail?.node_id ?? detail?.node);
        setState(node ?? activeNode, "error");
        activeNode = null;
    });
    api.addEventListener("execution_interrupted", () => {
        if (activeNode) setState(activeNode, "error");
        activeNode = null;
    });
    api.addEventListener("execution_success", () => {
        if (activeNode) setState(activeNode, "done");
        activeNode = null;
        setTimeout(() => {
            for (const node of themedNodes) {
                if (node.__vvExecutionState === "done") setState(node, "idle");
            }
        }, 2600);
    });
    animationTimer = setInterval(() => {
        if (activeNode?.__vvExecutionState === "active") {
            activeNode.setDirtyCanvas?.(true, true);
            app.graph?.setDirtyCanvas?.(true, false);
        }
    }, 90);
}

function themeGroups() {
    if (!graphIsKrea()) return;
    for (const group of app.graph?._groups ?? []) {
        const title = String(group.title ?? "").toUpperCase();
        if (title.includes("INTERNAL")) {
            group.color = "#17322b";
        } else if (title.includes("RELEASE GUIDE")) {
            group.color = "#2c2540";
        } else if (/^(00|02|05A|05C|05E|03A)/.test(title)) {
            group.color = "#3e3063";
        } else {
            group.color = "#225244";
        }
        if (Number.isFinite(group.font_size)) group.font_size = Math.max(16, Math.min(25, group.font_size));
    }
}

function themeGraph() {
    installCss();
    pruneThemedNodes();
    if (!graphIsKrea()) return;
    adoptNewKreaNodes();
    for (const node of app.graph?._nodes ?? []) applyTheme(node);
    themeGroups();
}

window.VelvetViceKreaDesign = Object.freeze({
    version: VERSION,
    palette: PALETTE,
    installCss,
    applyTheme,
    themeGraph,
});

app.registerExtension({
    name: "VelvetVice.KREA.FullSignatureDesignSystemV113",
    setup() {
        installCss();
        installExecutionStyling();
        setTimeout(themeGraph, 0);
    },
    nodeCreated(node) {
        // New rgthree Power LoRA nodes are created before pasted properties are
        // necessarily restored. Claim them from the already-active KREA graph
        // first, then apply the private KREA theme. A second pass catches
        // duplicate/paste timing without ever adopting nodes in an LTX graph.
        claimKreaThemeOwnership(node);
        applyTheme(node);
        setTimeout(() => {
            claimKreaThemeOwnership(node);
            applyTheme(node);
            themeGroups();
        }, 0);
    },
    loadedGraphNode(node) {
        applyTheme(node);
        setTimeout(themeGraph, 0);
    },
});
