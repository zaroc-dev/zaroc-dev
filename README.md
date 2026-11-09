# Arthur Aktamirov

Computer engineering student and trained backend developer from Germany.
I write Linux desktop software in Rust and run every machine I own on NixOS.

- **Now:** working student at nemetris GmbH
- **Studying:** B.Eng. Computer Engineering at Hochschule Albstadt-Sigmaringen
- **Before:** vocational training as a backend developer (Java, C#, RPG IV)

[zaroc.de](https://zaroc.de) · [LinkedIn](https://www.linkedin.com/in/arthur-aktamirov/) · [X](https://x.com/zaroc_dev)

## What I've built

| Project | What it is | Built with |
| --- | --- | --- |
| [rinka](https://github.com/zaroc-dev/rinka) | Living wallpapers for Wayland. One renderer draws the desktop natively and, compiled to WebAssembly, the editor's live preview. Imports Wallpaper Engine scenes and translates their shaders to WGSL. [Website](https://zaroc-dev.github.io/rinka/) | Rust, wgpu, WebGPU, FFmpeg |
| [yuki](https://github.com/zaroc-dev/yuki) | The desktop shell I use every day on niri: bar, launcher, lock screen, notification daemon, network and audio panels. | Quickshell, QML |
| [dotfiles](https://github.com/zaroc-dev/dotfiles) | One flake that builds all my machines, from a clean install to a working dev setup in a single command. | Nix, NixOS |
| [pruefungsvorbereitung](https://github.com/zaroc-dev/pruefungsvorbereitung) | Exam prep site for German IT apprentices (Fachinformatiker AP1 and AP2), used by other trainees. | MDX, Nextra |
| [kafka](https://github.com/zaroc-dev/kafka) | Semester planner for students at my university. | TypeScript, Next.js |

## This profile is a flake

```sh
nix run github:zaroc-dev/zaroc-dev
```

Prints the short version of this page in your terminal, built by a
[22-line flake](flake.nix).
