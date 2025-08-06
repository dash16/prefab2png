
# prefab2png

![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)
![Release](https://img.shields.io/badge/release-v0.5-green.svg)
![Pillow](https://img.shields.io/badge/made%20with-Pillow-yellow.svg)
![GitHub issues](https://img.shields.io/github/issues/dash16/prefab2png)

This Python script renders layered map images from game files used by the game **7 Days to Die**. It creates layers of labeled points of interest (POIs) using in-game data, suitable for editing or display.

**Version:** v0.7.1
**Author:** Dustin Newell  
**License:** AGPL-3.0

📄 Full documentation is now located in the [`docs/`](./docs/) folder.

- [Workflow Guide](./docs/workflow.md)
- [Full README](./docs/README.md)
- [Full Changelog](./docs/CHANGELOG.md)

---

To render a full map of a 7DTD world, start with the [workflow guide](./docs/workflow.md).

`prefab2png` is a modular rendering toolchain for visualizing terrain, POIs, and prefab data from 7 Days to Die.

### 🌍 Supported World Types:

* ✅ Navezgane (default)
* ✅ Pregen
* ✅ RWG (Random Gen Worlds)
* World sizes 2048–16384 (in testing)

> By default, the tool is configured to render Navezgane using OS-resolved paths. RWG, Pregen, and custom world support will be fully integrated, but require explicit CLI input for file paths.