<div align="center">

| [📖<br>Overview](README.md) | [📦<br>Releases](RELEASES.md) | [📜<br>Changelog](changelogs/changelog_1.0.0_to_2.0.1.md) | [🤝<br>Contributing](CONTRIBUTING.md) | [🛡️<br>Security](SECURITY.md) | [⚖️<br><nobr>Code of Conduct</nobr>](CODE_OF_CONDUCT.md) |
| :---: | :---: | :---: | :---: | :---: | :---: |

</div>

---

# Contributing to DimToggle

Thank you for your interest in contributing to DimToggle. DimToggle is an open-source, server-side Minecraft mod supporting Fabric, Forge, and NeoForge across multiple Minecraft releases.

## Code of Conduct

All contributors and participants are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting Issues

Before opening a new issue, search existing issues to see if your problem has already been reported.

* **Bug reports**: Use the [Bug report template](.github/ISSUE_TEMPLATE/bug.md). Provide exact Minecraft version, mod loader and version, DimToggle version, full server logs (`logs/latest.log`), and reproducible steps.
* **Questions**: Use the [Question template](.github/ISSUE_TEMPLATE/question.md).
* **Feature suggestions**: Use the [Feature suggestion template](.github/ISSUE_TEMPLATE/suggestion.md).

## Development Setup

DimToggle uses a dynamic multi-target architecture with Gradle and Python tooling.

### Prerequisites

* Git
* JDK 8, 17, and 21 installed and configured in your environment
* Python 3.8 or newer (for matrix orchestration tools)

### Building the Project

To validate target configurations:

```bash
python tools/kyro/template.py validate
```

To compile and build specific targets locally:

```bash
# Build a specific Minecraft version and loader
./gradlew build_1_20_1_fabric
./gradlew build_1_20_1_forge
./gradlew build_1_20_4_neoforge
```

Artifacts are output to `versions/<version>/<loader>/build/libs/`.

## Pull Request Guidelines

1. **Branching**: Create a feature branch from `dev/kyro-2.0.0` or the latest active development branch. Do not submit PRs directly to `main` without testing across loaders.
2. **Code style**:
   * Follow standard Java conventions.
   * Keep common logic in `common/` and loader-specific hooks in `versions/<version>/<loader>/`.
   * Maintain compatibility across all supported versions.
3. **Commit messages**:
   * Write clear, imperative commit summaries.
   * Do not include AI attribution tags or bot trailers.
4. **Testing**:
   * Verify that your code compiles across relevant Minecraft eras and loaders.
   * Test in-game on dedicated servers where applicable.
