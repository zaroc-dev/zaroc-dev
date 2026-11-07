#!/usr/bin/env python3
"""Render assets/terminal.svg: an animated terminal session for the profile README.

The SVG uses SMIL animations only (no JS, no external fonts), so it plays inside
GitHub's <img> sandbox. Every column is positioned on its own, so a fallback
monospace font can change glyph widths without breaking the layout.

Live data (recently pushed public repos, star count) comes from the GitHub API.
Set GITHUB_TOKEN to raise the rate limit; only public repos are ever listed.

    python3 scripts/terminal.py            # write assets/terminal.svg
    python3 scripts/terminal.py --static   # final frame without animation
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

USER = "zaroc-dev"
HOST = "hiyuki"
OUT = Path(__file__).resolve().parent.parent / "assets" / "terminal.svg"

# Repos never shown in the `ls` listing (forks and archived repos are skipped anyway).
EXCLUDE = {"zaroc-dev"}
MAX_REPOS = 6

# Layout
FONT = 14
CW = FONT * 0.6  # monospace advance width
LH = 21
PAD_X = 28
COLS = 98
WIDTH = round(PAD_X * 2 + COLS * CW)
BAR_H = 38

# Palette (night sky, matching the aurora line of yuki)
BG = "#0e1018"
BAR = "#141722"
BORDER = "#262a3b"
FG = "#c8d0ec"
DIM = "#5c6488"
BLUE = "#7aa2f7"
CYAN = "#7dcfff"
GREEN = "#9ece6a"
YELLOW = "#e0af68"
RED = "#f7768e"
PURPLE = "#bb9af7"
ORANGE = "#ff9e64"

LANG_COLORS = {
    "Rust": "#dea584", "QML": "#44a51c", "TypeScript": "#3178c6", "Nix": "#7e7eff",
    "Svelte": "#ff3e00", "Dart": "#00b4ab", "MDX": "#fcb32c", "Astro": "#ff5a03",
    "Python": "#3572a5", "C#": "#2fa84f", "Java": "#b07219", "Lua": "#6c8cd5",
    "C": "#a8b9cc", "Shell": "#89e051", "JavaScript": "#f1e05a", "HTML": "#e34c26",
}

Z_LOGO = [
    "########",
    "########",
    ".....###",
    "....###.",
    "...###..",
    "..###...",
    "########",
    "########",
]


# --------------------------------------------------------------------------- data

def fetch_repos() -> list[dict]:
    url = f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-terminal-renderer",
    })
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as res:
        return [r for r in json.load(res) if not r.get("private")]


def pick_recent(repos: list[dict]) -> list[dict]:
    shown = [
        r for r in repos
        if not r["fork"] and not r["archived"] and r["name"] not in EXCLUDE and r.get("description")
    ]
    shown.sort(key=lambda r: r["pushed_at"], reverse=True)
    return shown[:MAX_REPOS]


# ------------------------------------------------------------------------ drawing

Seg = tuple[str, str]  # (text, color)


def clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def tspans(segs: list[Seg]) -> str:
    return "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for t, c in segs)


class Terminal:
    def __init__(self, animate: bool):
        self.animate = animate
        self.body: list[str] = []
        self.defs: list[str] = []
        self.y = BAR_H + 30  # baseline of the next row
        self.t = 0.6  # timeline cursor in seconds
        self.clip_id = 0

    # A group that pops into view at time `at`.
    def reveal(self, inner: str, at: float) -> str:
        if not self.animate:
            return f"<g>{inner}</g>"
        return (
            f'<g opacity="0"><set attributeName="opacity" to="1" begin="{at:.2f}s" fill="freeze"/>'
            f"{inner}</g>"
        )

    def text(self, x: float, y: float, segs: list[Seg], extra: str = "") -> str:
        return f'<text x="{x:.1f}" y="{y}" {extra}>{tspans(segs)}</text>'

    def prompt(self, command: str, cwd: str = "~") -> None:
        p = [("arthur", GREEN), ("@", DIM), (HOST, BLUE), (f" {cwd} ", CYAN), ("$ ", PURPLE)]
        plen = sum(len(t) for t, _ in p)
        cx = PAD_X + plen * CW
        y = self.y
        cmd = self.text(cx, y, [(command, FG)], 'class="cmd"')
        if self.animate:
            self.clip_id += 1
            cid = f"type{self.clip_id}"
            step = 0.055
            start = self.t + 0.35
            widths = ";".join(f"{i * CW:.1f}" for i in range(len(command) + 1))
            dur = step * (len(command) + 1)
            self.defs.append(
                f'<clipPath id="{cid}"><rect x="{cx - 1:.1f}" y="{y - FONT - 2}" height="{LH}" width="0">'
                f'<animate attributeName="width" values="{widths};{WIDTH}" calcMode="discrete" '
                f'begin="{start:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>'
            )
            cmd = f'<g clip-path="url(#{cid})">{cmd}</g>'
            self.body.append(self.reveal(self.text(PAD_X, y, p) + cmd, self.t))
            self.t = start + dur + 0.3
        else:
            self.body.append(self.text(PAD_X, y, p) + cmd)
        self.y += LH

    def out(self, segs: list[Seg], x: float = PAD_X) -> None:
        self.body.append(self.reveal(self.text(x, self.y, segs), self.t))
        self.y += LH
        self.t += 0.035

    def gap(self, rows: float = 0.5, pause: float = 0.5) -> None:
        self.y += round(LH * rows)
        self.t += pause

    def fastfetch(self, info: list[list[Seg]]) -> None:
        top = self.y - FONT
        px, pg = 14, 2
        logo_w = len(Z_LOGO[0]) * (px + pg)
        cells = []
        for r, row in enumerate(Z_LOGO):
            for c, ch in enumerate(row):
                if ch != "#":
                    continue
                x = PAD_X + 6 + c * (px + pg)
                y = top + 8 + r * (px + pg)
                shadow = f'<rect x="{x + 3}" y="{y + 3}" width="{px}" height="{px}" rx="2" fill="#1d2133"/>'
                cell = f'<rect x="{x}" y="{y}" width="{px}" height="{px}" rx="2" fill="url(#zgrad)"/>'
                if self.animate:
                    at = self.t + (r + c) * 0.03
                    cell = (
                        f'<g opacity="0" transform="translate(0 0)">'
                        f'<set attributeName="opacity" to="1" begin="{at:.2f}s" fill="freeze"/>{cell}</g>'
                    )
                cells.append(shadow + cell)
        self.defs.append(
            f'<linearGradient id="zgrad" gradientUnits="userSpaceOnUse" x1="{PAD_X}" y1="{top}" '
            f'x2="{PAD_X + logo_w}" y2="{top + logo_w}">'
            f'<stop offset="0" stop-color="{PURPLE}"/><stop offset="0.55" stop-color="{BLUE}"/>'
            f'<stop offset="1" stop-color="{CYAN}"/></linearGradient>'
        )
        self.body.append(self.reveal("".join(cells), self.t))
        ix = PAD_X + logo_w + 44
        for segs in info:
            self.out(segs, x=ix)
        # fastfetch colour blocks
        blocks = "".join(
            f'<rect x="{ix + i * 26:.1f}" y="{self.y - FONT + 4}" width="22" height="12" rx="2" fill="{c}"/>'
            for i, c in enumerate([DIM, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, FG])
        )
        self.body.append(self.reveal(blocks, self.t))
        self.y += LH
        self.t += 0.1

    def cursor(self) -> None:
        p = [("arthur", GREEN), ("@", DIM), (HOST, BLUE), (" ~ ", CYAN), ("$ ", PURPLE)]
        plen = sum(len(t) for t, _ in p)
        blink = (
            '<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" '
            'repeatCount="indefinite"/>' if self.animate else ""
        )
        rect = (
            f'<rect x="{PAD_X + plen * CW:.1f}" y="{self.y - FONT + 1}" width="{CW:.1f}" '
            f'height="{FONT + 3}" fill="{FG}">{blink}</rect>'
        )
        self.body.append(self.reveal(self.text(PAD_X, self.y, p) + rect, self.t))
        self.y += LH

    def svg(self) -> str:
        height = self.y + 4
        aurora_anim = (
            '<animateTransform attributeName="gradientTransform" type="translate" '
            f'values="-{WIDTH} 0;{WIDTH} 0" dur="9s" repeatCount="indefinite"/>' if self.animate else ""
        )
        workspaces = "".join(
            f'<rect x="{18 + i * 14 + (10 if i > 0 else 0)}" y="{BAR_H / 2 - 4}" '
            f'width="{20 if i == 0 else 8}" height="8" rx="4" fill="{BLUE if i == 0 else DIM}"/>'
            for i in range(3)
        )
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Terminal session on {HOST}: fastfetch, recently pushed projects, and a homelab that stays private">
<defs>
<linearGradient id="aurora" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{WIDTH}" y2="0" spreadMethod="repeat">
<stop offset="0" stop-color="{PURPLE}" stop-opacity="0.15"/><stop offset="0.3" stop-color="{BLUE}"/>
<stop offset="0.5" stop-color="{CYAN}"/><stop offset="0.7" stop-color="{GREEN}" stop-opacity="0.6"/>
<stop offset="1" stop-color="{PURPLE}" stop-opacity="0.15"/>{aurora_anim}</linearGradient>
<clipPath id="win"><rect width="{WIDTH}" height="{height}" rx="14"/></clipPath>
{"".join(self.defs)}
</defs>
<style>text{{font-family:'JetBrains Mono','JetBrainsMono Nerd Font','SF Mono',Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace;font-size:{FONT}px;white-space:pre}}.title{{font-size:12px}}</style>
<g clip-path="url(#win)">
<rect width="{WIDTH}" height="{height}" fill="{BG}"/>
<rect width="{WIDTH}" height="{BAR_H}" fill="{BAR}"/>
<rect y="{BAR_H - 2}" width="{WIDTH}" height="2" fill="url(#aurora)"/>
{workspaces}
<text class="title" x="{WIDTH / 2:.1f}" y="{BAR_H / 2 + 4}" text-anchor="middle" fill="{DIM}">kitty · arthur@{HOST}: ~</text>
{"".join(self.body)}
</g>
<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="14" fill="none" stroke="{BORDER}"/>
</svg>
"""


# --------------------------------------------------------------------------- main

def main() -> None:
    animate = "--static" not in sys.argv
    repos = fetch_repos()
    recent = pick_recent(repos)
    public = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in public)

    t = Terminal(animate)

    def kv(key: str, *value: Seg) -> list[Seg]:
        return [(f"{key:<10}", BLUE), *value]

    t.prompt("fastfetch")
    t.gap(0.25, 0.2)
    t.fastfetch([
        [("arthur", GREEN), ("@", DIM), (HOST, BLUE), ("  aka ZAROC", DIM)],
        [("-" * 26, DIM)],
        kv("OS", ("NixOS", FG), ("  flakes all the way down", DIM)),
        kv("WM", ("niri", FG)),
        kv("Shell", ("yuki", FG), ("  my own, Quickshell + QML", DIM)),
        kv("Wallpaper", ("rinka", FG), ("  my own, Rust + wgpu", DIM)),
        kv("Editor", ("neovim", FG)),
        kv("Work", ("working student @ nemetris GmbH", FG)),
        kv("Uni", ("Computer Engineering @ HS Albstadt-Sigmaringen", FG)),
        kv("Before", ("vocational training as backend dev", FG), ("  (Java, C#, RPG IV)", DIM)),
        kv("Langs", ("Rust · TypeScript · Nix · QML · Svelte · C#", FG)),
        kv("GitHub", (f"{len(public)} public repos · ★ {stars}", FG)),
        kv("Homelab", ("● online", GREEN), ("  (that's all you get)", DIM)),
    ])
    t.gap(0.4, 0.6)

    t.prompt("ls -t ~/src | head")
    name_w = max(len(r["name"]) for r in recent) + 2
    lang_w = 13
    for r in recent:
        lang = r.get("language") or "-"
        date = datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")).strftime("%b %d")
        desc_w = COLS - name_w - lang_w - 8
        desc = r["description"].removeprefix(f"{r['name']}: ")
        t.out([
            (f"{r['name'] + '/':<{name_w}}", BLUE),
            ("● ", LANG_COLORS.get(lang, DIM)),
            (f"{lang:<{lang_w - 2}}", FG),
            (f"{date}  ", DIM),
            (clip(desc, desc_w), FG),
        ])
    t.gap(0.4, 0.6)

    t.prompt("ssh homelab")
    t.t += 0.5
    t.out([("arthur@homelab: ", RED), ("Permission denied (publickey).", FG)])
    t.out([("# it's where most of my evenings go. it stays off GitHub for good reasons.", DIM)])
    t.gap(0.4, 0.5)
    t.cursor()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(t.svg(), encoding="utf-8")
    print(f"wrote {OUT} ({len(recent)} repos, {stars} stars)")


if __name__ == "__main__":
    main()
