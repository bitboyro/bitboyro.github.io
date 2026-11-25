"""Layered A/B secret-flow figures, in two layouts.

wide: steps are columns, layers (Java heap / native / OS) are horizontal bands.
tall: the same figure turned on its side for phones: steps are rows, layers are columns.

Numbered chips are plaintext copies placed in the layer where they live; a line threads them in
order. Writes secret-copies-{client,server}.svg and secret-copies-{client,server}-mobile.svg.
"""
import sys
from html import escape

INK, INK2, MUTED, BG = "#1A1714", "#5A4F47", "#8C8279", "#FDFCFB"
BAND = {"heap": "#F3ECE4", "native": "#E7F0EB", "os": "#F7F5F2"}
PLAIN, GREY, HANDLE, WIPE = "#B4462B", "#9A9087", "#6B4F35", "#2E6B4F"
SANS = "'DM Sans',system-ui,-apple-system,'Segoe UI',sans-serif"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"
CHIP = {"heap": ("#F6DCD2", PLAIN, "#7A2A16"), "native": ("#ECE8E3", GREY, "#4A423B"),
        "wiped": ("#DCEBE2", WIPE, "#1F4D38"), "public": ("#FFFFFF", "#B9AFA5", "#6F665E"),
        "os": ("#FFFFFF", "#D9D2CA", INK)}
CH = 22  # chip height


class Canvas:
    def __init__(self):
        self.o = []

    def t(self, x, y, s, size=13, w=400, fill=INK, anchor="start", mono=False, italic=False):
        st = ' font-style="italic"' if italic else ''
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" '
                      f'text-anchor="{anchor}" font-family="{MONO if mono else SANS}"{st}>{escape(s)}</text>')

    def path(self, d, color, dash=None, w=2.0, marker=None):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        m = f' marker-end="url(#{marker})"' if marker else ''
        self.o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round"{da}{m}/>')

    def rect(self, x, y, w, h, fill, rx=8, extra=""):
        self.o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{extra}/>')

    def chip(self, x, y, label, kind, size=11.5):
        fill, stroke, txt = CHIP[kind]
        w = chip_w(label, size)
        dash = ' stroke-dasharray="3 3"' if kind == "public" else ''
        self.rect(x, y, w, CH, fill, 6 if kind == "os" else CH / 2, f' stroke="{stroke}"{dash}')
        self.t(x + 10, y + 15, label, size, 600, txt)
        return w

    def wipe_icon(self, x, y):
        self.o.append(f'<g transform="translate({x:.1f},{y:.1f})"><circle r="6.5" fill="{WIPE}"/>'
                      f'<path d="M-2.8-2.8L2.8 2.8M2.8-2.8L-2.8 2.8" stroke="#fff" stroke-width="1.7"/></g>')

    def step_badge(self, x, y, n, r=10):
        self.o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{INK}"/>')
        self.t(x, y + 4.3, str(n), 12, 700, "#FFFFFF", "middle")

    def svg(self, W, H, title, desc):
        m = lambda i, c: (f'<marker id="{i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" '
                          f'markerHeight="6.5" orient="auto"><path d="M0 0L10 5L0 10z" fill="{c}"/></marker>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}" role="img" aria-labelledby="t d">'
                f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
                f'<defs>{m("h", HANDLE)}{m("g", GREY)}</defs><rect width="{W}" height="{H:.0f}" fill="{BG}"/>'
                + "\n".join(self.o) + "</svg>")


def chip_w(label, size=11.5):
    return len(label) * size * 0.52 + 20


def lbl(it, tall):
    return it.get("tall", it["label"]) if tall else it["label"]


def thread(c, pos, flow, vertical, anchor=None):
    """Draw the copy path behind the chips. pos: id -> (x, y, w)."""
    anchor = anchor or (lambda i: (pos[i][0] + 24, pos[i][1] + CH / 2))
    for (a_id, _), (b_id, kind) in zip(flow, flow[1:]):
        ax, ay, aw = pos[a_id]
        bx, by, bw = pos[b_id]
        (acx, acy), (bcx, bcy) = anchor(a_id), anchor(b_id)
        col = PLAIN if kind == "p" else GREY
        if abs(acx - bcx) < 1:
            d = f"M{acx:.1f} {acy:.1f}V{bcy:.1f}"
        elif abs(acy - bcy) < 1:
            d = f"M{acx:.1f} {acy:.1f}H{bcx:.1f}"
        elif vertical:
            mid = (ay + CH + by) / 2 if by > ay + CH else acy
            d = f"M{acx:.1f} {acy:.1f}V{mid:.1f}H{bcx:.1f}V{bcy:.1f}"
        else:
            mid = (ax + aw + bx) / 2 if bx > ax + aw else acx
            d = f"M{acx:.1f} {acy:.1f}H{mid:.1f}V{bcy:.1f}H{bcx:.1f}"
        c.path(d, col, None, 2.4)


LEGEND = [("line", PLAIN, None, "plaintext path"), ("line", GREY, None, "encrypted"),
          ("line", HANDLE, "2 4", "handle only"), ("chip", "heap", "heap copy, not wiped"),
          ("chip", "native", "native copy, not wiped"), ("chip", "wiped", "native copy, wiped"),
          ("chip", "public", "not secret")]
FOOT = "Numbered chips are plaintext copies in the order they appear; counts are a floor, not a census."


def legend_item(c, x, y, item):
    if item[0] == "line":
        _, color, dash, label = item
        c.path(f"M{x} {y}h26", color, dash, 2.4 if not dash else 1.5, "h" if dash else None)
        c.t(x + 33, y + 4.5, label, 12, 500, INK2)
        return 33 + len(label) * 6.2
    _, kind, label = item
    fill, stroke, _ = CHIP[kind]
    dash = ' stroke-dasharray="3 3"' if kind == "public" else ''
    c.rect(x, y - 7, 24, 14, fill, 7, f' stroke="{stroke}"{dash}')
    c.t(x + 31, y + 4.5, label, 12, 500, INK2)
    return 31 + len(label) * 6.2


# ------------------------------------------------------------------------------------------ wide
def wide(fig):
    W, LX, COL0 = 1100, 20, 140
    HEAP, NAT, OS, GAP = 82, 62, 34, 6
    c = Canvas()
    steps = fig["steps"]
    colw = (W - 20 - COL0) / len(steps)
    c.t(LX, 26, fig["title"], 17, 700)
    y = 40
    for i, s in enumerate(steps):
        x = COL0 + i * colw + 12
        c.step_badge(x + 10, y + 12, i + 1)
        c.t(x + 26, y + 16.5, s, 12.5, 600)
    y += 34
    for p in (fig["a"], fig["b"]):
        c.t(LX, y + 13, p["head"], 14, 700)
        c.t(W - 20, y + 13, p["total"], 12.5, 700, INK, "end")
        y += 22
        tops = {}
        for layer, h, (a, b) in zip(("heap", "native", "os"), (HEAP, NAT, OS), p["labels"]):
            extra = ' stroke-dasharray="4 4" stroke="#CFC3B6"' if layer == "os" else ''
            c.rect(LX, y, W - 40, h, BAND[layer], 8, extra)
            c.t(LX + 12, y + h / 2 + 4.5, a, 12, 700)
            tops[layer] = y
            y += h + GAP
        by = tops["native"] - GAP / 2
        c.path(f"M{LX} {by}H{W-20}", PLAIN if p.get("boundary") else "#D8CDC1", "8 5", 1.4)
        if p.get("boundary"):
            c.t(W - 26, tops["native"] - 9, p["boundary"], 12, 600, PLAIN, "end", italic=True)
        for i in range(1, len(steps)):
            x = COL0 + i * colw
            c.o.append(f'<line x1="{x:.1f}" y1="{tops["heap"]+6}" x2="{x:.1f}" y2="{tops["os"]+OS-6}" stroke="#FFFFFF" stroke-width="2"/>')
        items = p["items"]
        codes = {it["step"]: it for it in items if it["kind"] == "code"}
        stacked = {(it["step"], it["layer"]) for it in items if it.get("row", 0) == 1}
        pos = {}
        for it in items:
            if it["kind"] in ("code", "note"):
                continue
            x = COL0 + (it["step"] - 1) * colw + 12
            r = it.get("row", 0)
            if it["kind"] == "public":
                x, yy = x + 54, tops["heap"] + 52
            elif it["layer"] == "heap":
                yy = tops["heap"] + (25 if it["step"] in codes else 12) + r * 28
            elif it["layer"] == "native":
                yy = tops["native"] + (6 + r * 28 if (it["step"], "native") in stacked else (NAT - CH) / 2)
            else:
                yy = tops["os"] + (OS - CH) / 2
            pos[it["id"]] = (x, yy, chip_w(lbl(it, False)))
        thread(c, pos, p["flow"], vertical=False)
        for it in items:
            if it["kind"] == "public":
                sx, sy, sw = pos[it["src"]]
                px, py, pw = pos[it["id"]]
                c.path(f"M{sx+sw:.1f} {sy+CH/2:.1f}H{px+pw/2:.1f}V{py+CH+3:.1f}", GREY, None, 2.2, "g")
        for step, it in codes.items():
            x = COL0 + (step - 1) * colw + 12
            c.t(x, tops["heap"] + 17, it["label"], 11, 500, INK, mono=True)
            for tgt in it.get("handles", []):
                tx, ty, _ = pos[tgt]
                c.path(f"M{x+40} {tops['heap']+22}V{ty-3:.1f}", HANDLE, "2 4", 1.4, "h")
        for it in items:
            if it["kind"] != "note":
                continue
            x = COL0 + (it["step"] - 1) * colw + 12 + it.get("dx", 0)
            yy = tops[it["layer"]] + it.get("dy", 20)
            if it.get("wipe"):
                c.wipe_icon(x + 7, yy - 4.5)
                x += 19
            for k, line in enumerate(it["label"].split("\n")):
                c.t(x, yy + k * 16, line, 13, 700, WIPE if it.get("wipe") else (PLAIN if it.get("bad") else INK2))
        for it in items:
            if it.get("id") in pos:
                x, yy, _ = pos[it["id"]]
                c.chip(x, yy, lbl(it, False), it["kind"])
        y += 14
    lx = LX
    for item in LEGEND:
        lx += legend_item(c, lx, y + 4, item) + 18
    return c.svg(W, y + 22, fig["title"], fig["desc"])


# ------------------------------------------------------------------------------------------ tall
def tall(fig):
    W = 420
    COLS = {"heap": (12, 172), "native": (178, 152), "os": (334, 74)}
    c = Canvas()
    c.t(12, 24, fig["title"], 15, 700)
    y = 36
    for p in (fig["a"], fig["b"]):
        c.t(12, y + 16, p["head"], 13.5, 700)
        c.t(12, y + 33, p["total"], 12, 700, INK2)
        y += 44
        top = y
        rows = []
        # measure rows
        yy = y + 30
        for si in range(len(fig["steps"])):
            step = si + 1
            items = [it for it in p["items"] if it["step"] == step]
            h = {"heap": 0, "native": 0, "os": 0}
            for it in items:
                k = it["kind"]
                if k == "code":
                    h["heap"] = max(h["heap"], 14)
                elif k == "note":
                    n = len(it.get("tall", it["label"]).split("\n"))
                    base = h[it["layer"]] if it["layer"] == "heap" and it.get("after_chips") else 0
                    h[it["layer"]] = max(h[it["layer"]], it.get("tall_dy", 0) + n * 16 + 4)
                else:
                    layer = "heap" if k == "public" else it["layer"]
                    off = 14 if (layer == "heap" and any(i["kind"] == "code" for i in items)) else 0
                    if k == "public":
                        off += 28 * sum(1 for i in items if i["layer"] == "heap" and i["kind"] not in ("code", "note", "public"))
                    h[layer] = max(h[layer], off + 6 + it.get("row", 0) * 28 + CH)
            rh = 24 + max(h.values()) + 12
            rows.append((yy, rh))
            yy += rh
        bottom = yy
        # column bands
        for layer, (cx, cw) in COLS.items():
            extra = ' stroke-dasharray="4 4" stroke="#CFC3B6"' if layer == "os" else ''
            c.rect(cx, top, cw, bottom - top, BAND[layer], 8, extra)
        for layer, (a, b) in zip(("heap", "native", "os"), p["labels"]):
            cx, cw = COLS[layer]
            c.t(cx + 8, top + 18, a if layer != "os" else "OS", 11.5, 700)
        bx = COLS["native"][0] - 3
        c.path(f"M{bx} {top}V{bottom}", PLAIN if p.get("boundary") else "#D8CDC1", "8 5", 1.4)
        pos, codes = {}, {}
        for si, (ry, rh) in enumerate(rows):
            step = si + 1
            if si:
                c.o.append(f'<line x1="12" y1="{ry:.1f}" x2="{W-12}" y2="{ry:.1f}" stroke="#FFFFFF" stroke-width="2"/>')
            c.step_badge(24, ry + 13, step, 9)
            c.t(38, ry + 17, fig.get("steps_tall", fig["steps"])[si], 12, 600)
            items = [it for it in p["items"] if it["step"] == step]
            has_code = any(it["kind"] == "code" for it in items)
            heap_chips = [it for it in items if it["layer"] == "heap" and it["kind"] not in ("code", "note", "public")]
            for it in items:
                k = it["kind"]
                if k == "code":
                    codes[step] = (it, ry)
                    continue
                if k == "note":
                    continue
                layer = it["layer"]
                cx = COLS[layer][0] + 8
                r = it.get("row", 0)
                if k == "public":
                    cy = ry + 24 + (14 if has_code else 0) + 6 + 28 * len(heap_chips)
                elif layer == "heap":
                    cy = ry + 24 + (14 if has_code else 0) + 6 + r * 28
                else:
                    cy = ry + 24 + 6 + r * 28 + (14 if has_code and layer == "native" and r == 0 and not any(
                        i.get("row", 0) == 1 and i["layer"] == "native" for i in items) else 0)
                pos[it["id"]] = (cx, cy, chip_w(lbl(it, True), 11))
        layer_of = {it["id"]: it["layer"] for it in p["items"] if it.get("id")}
        lane = {k: cx + cw - 16 for k, (cx, cw) in COLS.items()}
        def anchor(i):
            x, y_, w = pos[i]
            if layer_of[i] == "os":
                return x + 6, y_ + CH / 2
            return lane[layer_of[i]], y_ + CH / 2
        for a_id, kind in p["flow"]:
            if layer_of[a_id] != "os":
                x, y_, w = pos[a_id]
                c.path(f"M{x+w-4:.1f} {y_+CH/2:.1f}H{lane[layer_of[a_id]]:.1f}", PLAIN, None, 2.4)
        thread(c, pos, p["flow"], vertical=True, anchor=anchor)
        for it in p["items"]:
            if it["kind"] == "public":
                sx, sy, sw = pos[it["src"]]
                px, py, pw = pos[it["id"]]
                mid = COLS["native"][0] - 3
                c.path(f"M{sx:.1f} {sy+CH/2:.1f}H{mid}V{py+CH/2:.1f}H{px+pw+3:.1f}", GREY, None, 2.0, "g")
        for step, (it, ry) in codes.items():
            x = COLS["heap"][0] + 8
            code = it.get("tall", it["label"])
            c.t(x, ry + 34, code, 11, 500, INK, mono=True)
            for tgt in it.get("handles", []):
                tx, ty, _ = pos[tgt]
                sx = x + len(code) * 6.6 + 4
                c.path(f"M{sx:.1f} {ry+30:.1f}H{bx+6:.1f}V{ty+CH/2:.1f}H{tx-3:.1f}", HANDLE, "2 4", 1.3, "h")
        for it in p["items"]:
            if it["kind"] != "note":
                continue
            ry = rows[it["step"] - 1][0]
            x = COLS[it["layer"]][0] + 8
            yy = ry + 24 + 12 + it.get("tall_dy", 0)
            if it.get("wipe"):
                c.wipe_icon(x + 6, yy - 4)
                x += 17
            for k, line in enumerate(it.get("tall", it["label"]).split("\n")):
                c.t(x, yy + k * 16, line, 13, 700, WIPE if it.get("wipe") else (PLAIN if it.get("bad") else INK2))
        for it in p["items"]:
            if it.get("id") in pos:
                x, yy, _ = pos[it["id"]]
                c.chip(x, yy, lbl(it, True), it["kind"], 11)
        y = bottom + 22
    if fig["b"].get("boundary"):
        c.path(f"M12 {y}h26", PLAIN, "8 5", 1.4)
        c.t(45, y + 4.5, "B: secret bytes stay right of this line", 12, 500, INK2)
        y += 22
    for i, item in enumerate(LEGEND):
        legend_item(c, 12 + (i % 2) * 200, y + (i // 2) * 22, item)
    y += ((len(LEGEND) + 1) // 2) * 22
    return c.svg(W, y + 4, fig["title"], fig["desc"])


# ------------------------------------------------------------------------------------------ data
CLIENT = dict(
    title="Client · send a token from a file",
    desc="Client flow, the usual Spring way (A) against Rust-owned buffers (B). A: four copies, all on the "
         "Java heap, none wiped. B: three copies, none on the heap, all wiped.",
    foot="",
    steps=["Load the token", "Build the header", "Encode, encrypt, send", "Finish"],
    steps_tall=["Load the token", "Build the header", "Encode and send", "Finish"],
    a=dict(head="A · the usual Spring way", sub="RestClient on the JDK HttpClient",
           total="4 copies · 4 on the heap · 0 wiped",
           labels=[("JAVA HEAP", ""), ("NATIVE", ""), ("OS + NET", "")],
           items=[
               dict(id="f", step=1, layer="os", kind="os", label="token file · page cache", tall="file"),
               dict(id="c1", step=1, layer="heap", kind="heap", label="1 · file String"),
               dict(id="c2", step=1, layer="heap", kind="heap", label="2 · stripped String", row=1),
               dict(id="c3", step=2, layer="heap", kind="heap", label="3 · header String"),
               dict(id="c4", step=3, layer="heap", kind="heap", label="4 · header bytes"),
               dict(id="s", step=3, layer="os", kind="os", label="socket → network", tall="socket"),
               dict(step=1, layer="heap", kind="code", label="Files.readString(p).strip()", tall="readString(p).strip()"),
               dict(step=2, layer="heap", kind="code", label='.header(AUTH, "Bearer " + t)', tall='"Bearer " + t'),
               dict(step=3, layer="heap", kind="code", label=".retrieve()"),
               dict(step=4, layer="heap", kind="note", label="GC decides\nwhen to wipe", bad=True, dy=38),
           ],
           flow=[("f", None), ("c1", "p"), ("c2", "p"), ("c3", "p"), ("c4", "p"), ("s", "g")]),
    b=dict(head="B · Java decides, Rust holds the bytes", sub="handles in Java, buffers in Rust",
           total="3 copies · 0 on the heap · 3 wiped", boundary="secret bytes stay below",
           labels=[("JAVA HEAP", ""), ("RUST · NATIVE", ""), ("OS + NET", "")],
           items=[
               dict(id="f", step=1, layer="os", kind="os", label="token file · page cache", tall="file"),
               dict(id="c1", step=1, layer="native", kind="wiped", label="1 · token buffer"),
               dict(id="c2", step=2, layer="native", kind="wiped", label="2 · header value"),
               dict(id="c3", step=3, layer="native", kind="wiped", label="3 · write buffers"),
               dict(id="s", step=3, layer="os", kind="os", label="socket → network", tall="socket"),
               dict(step=1, layer="heap", kind="code", label="NativeSecret.fromFile(p)", tall="fromFile(p)", handles=["c1"]),
               dict(step=2, layer="heap", kind="code", label=".secretHeader(…, token)", tall="secretHeader(…)", handles=["c2"]),
               dict(step=3, layer="heap", kind="code", label="client.getStream(req)", tall="getStream(req)", handles=["c3"]),
               dict(step=4, layer="heap", kind="code", label="token.close()"),
               dict(step=4, layer="native", kind="note", label="all 3 wiped", wipe=True, dy=36),
           ],
           flow=[("f", None), ("c1", "p"), ("c2", "p"), ("c3", "p"), ("s", "g")]))

SERVER = dict(
    title="Server · check a token, pass a password on",
    desc="Gateway route, the usual Spring way (A) against Rust-owned buffers (B). A: six copies, four on the "
         "Java heap, none wiped. B: seven copies, none on the heap, all wiped.",
    foot="",
    steps=["Receive", "Read token", "Read password", "Check token", "Forward", "Finish"],
    a=dict(head="A · the usual Spring way", sub="WebFlux on Reactor Netty, Jackson",
           total="6 copies · 4 on the heap · 0 wiped",
           labels=[("JAVA HEAP", ""), ("NETTY · NATIVE", ""), ("OS + NET", "")],
           items=[
               dict(id="in", step=1, layer="os", kind="os", label="socket"),
               dict(id="c1", step=1, layer="native", kind="native", label="1 · read buffers"),
               dict(id="c2", step=2, layer="heap", kind="heap", label="2 · header String"),
               dict(id="c3", step=3, layer="heap", kind="heap", label="3 · password"),
               dict(id="c4", step=4, layer="heap", kind="heap", label="4 · expected"),
               dict(id="c5", step=5, layer="heap", kind="heap", label="5 · JSON bytes"),
               dict(id="c6", step=5, layer="native", kind="native", label="6 · write buffers"),
               dict(id="out", step=5, layer="os", kind="os", label="socket"),
               dict(step=2, layer="heap", kind="code", label="getFirst(AUTH)"),
               dict(step=3, layer="heap", kind="code", label="bodyToMono(…)"),
               dict(step=4, layer="heap", kind="code", label="expected.equals(t)", tall="equals(t)"),
               dict(step=5, layer="heap", kind="code", label="bodyValue(login)", tall="bodyValue(…)"),
               dict(step=6, layer="heap", kind="note", label="GC decides\nwhen to wipe", bad=True, dy=38),
           ],
           flow=[("in", None), ("c1", "p"), ("c2", "p"), ("c3", "p"), ("c4", "p"), ("c5", "p"), ("c6", "p"), ("out", "g")]),
    b=dict(head="B · Java decides, Rust holds the bytes", sub="handles in Java, buffers in Rust",
           total="7 copies · 0 on the heap · 7 wiped", boundary="secret bytes stay below",
           labels=[("JAVA HEAP", ""), ("RUST · NATIVE", ""), ("OS + NET", "")],
           items=[
               dict(id="in", step=1, layer="os", kind="os", label="socket"),
               dict(id="c1", step=1, layer="native", kind="wiped", label="1 · read buffers"),
               dict(id="c2", step=2, layer="native", kind="wiped", label="2 · header value"),
               dict(id="c3", step=3, layer="native", kind="wiped", label="3 · body"),
               dict(id="c4", step=3, layer="native", kind="wiped", label="4 · password", row=1),
               dict(id="pub", step=3, layer="heap", kind="public", label="public JSON", src="c3"),
               dict(id="c5", step=4, layer="native", kind="wiped", label="5 · expected"),
               dict(id="c6", step=5, layer="native", kind="wiped", label="6 · outbound body"),
               dict(id="c7", step=5, layer="native", kind="wiped", label="7 · write buffers", row=1),
               dict(id="out", step=5, layer="os", kind="os", label="socket"),
               dict(step=2, layer="heap", kind="code", label="header(ex, …)", handles=["c2"]),
               dict(step=3, layer="heap", kind="code", label="bodyJson(ex, …)", handles=["c3"]),
               dict(step=4, layer="heap", kind="code", label="bearerEquals(…)", handles=["c5"]),
               dict(step=5, layer="heap", kind="code", label="SecretBody…build()", tall="SecretBody…build()", handles=["c6"]),
               dict(step=6, layer="heap", kind="code", label="close()"),
               dict(step=6, layer="native", kind="note", label="all 7 wiped", wipe=True, dy=36),
           ],
           flow=[("in", None), ("c1", "p"), ("c2", "p"), ("c3", "p"), ("c4", "p"), ("c5", "p"), ("c6", "p"), ("c7", "p"), ("out", "g")]))

if __name__ == "__main__":
    out = sys.argv[1]
    for name, fig in (("client", CLIENT), ("server", SERVER)):
        open(f"{out}/secret-copies-{name}.svg", "w").write(wide(fig))
        open(f"{out}/secret-copies-{name}-mobile.svg", "w").write(tall(fig))
