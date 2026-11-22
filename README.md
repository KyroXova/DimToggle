# DimToggle

A high-performance dimension access control and dimension locking mod for Minecraft across Forge, Fabric, and NeoForge.

DimToggle allows server administrators and modpack creators to lock, unlock, restrict, and manage access to any dimension (vanilla or modded) dynamically or permanently.

## Key Features

- **Dynamic Dimension Locking**: Lock any dimension permanently or for a specific duration (e.g. `2d`, `12h30m`, `45m`).
- **Timed Expiry & Announcements**: Automatically unlocks dimensions when the timer expires and broadcasts server-wide notifications.
- **Granular Access Control**:
  - **Operator Bypass**: Configurable (`allowOps`) permission level 2 access.
  - **Specific Users**: Allowlist individual players via commands (`/dimtoggle allow`) or configuration.
  - **Specific Groups**: Allowlist player groups via commands (`/dimtoggle allowgroup`), LuckPerms groups, or Minecraft Scoreboard Teams.
  - **LuckPerms Integration**: Full integration supporting permission nodes (`dimtoggle.<namespace>.<dimension>`, `dimtoggle.*`, `dimtoggle.bypass`).
- **Safe Enforcement**: Blocks unauthorized travel, provides rate-limited notification messages, and safely relocates players (`teleportToSpawn`) to avoid portal trap loops or void falls.
- **Convenient Teleport**: Safe dimension teleportation command (`/dt <player> <dimension>`).

## Commands

- `/dimtoggle list`: View all currently locked dimensions, their lock durations, and remaining times.
- `/dimtoggle lock <dimension> [duration]`: Lock a dimension permanently or for a timed duration (e.g., `1d2h`, `30m`).
- `/dimtoggle unlock <dimension>`: Unlock a dimension for all players.
- `/dimtoggle enable <dimension>`: Lock alias (adds dimension to restricted list).
- `/dimtoggle disable <dimension>`: Unlock alias (removes dimension from restricted list).
- `/dimtoggle allow <dimension> <player>`: Permit a specific user to enter a locked dimension.
- `/dimtoggle disallow <dimension> <player>`: Remove a user from a dimension's allowlist.
- `/dimtoggle allowgroup <dimension> <group>`: Permit a specific group (LuckPerms or Scoreboard Team) to enter.
- `/dimtoggle disallowgroup <dimension> <group>`: Remove a group from a dimension's allowlist.
- `/dimtoggle reload`: Reload `dimtoggle.json` configuration from disk.
- `/dt <player> <dimension>`: Safely teleport players to a dimension spawn position.

## Configuration (`config/dimtoggle.json`)

```json
{
  "enableLuckPerms": true,
  "teleportToSpawn": true,
  "allowOps": true,
  "restrictedDimensions": [
    "minecraft:the_end",
    "minecraft:the_nether"
  ],
  "allowedUsers": {
    "minecraft:the_end": ["Alice", "Bob"]
  },
  "allowedGroups": {
    "minecraft:the_end": ["vip", "donator"]
  }
}
```

`restrictedDimensions` seeds the per-world lock state the first time that world
starts with DimToggle. After that, use the lock and unlock commands; reloading
the JSON does not replace existing world locks. Timed locks use wall-clock time
and can expire while the server is stopped.

## Architecture & Multi-Version Matrix

DimToggle is built on a shared-core architecture:
- `common/src/main/java`: Platform-independent dimension lock management (`DimensionLocks`), access rules (`AccessPolicy`), duration parsing (`LockDuration`), LuckPerms reflection bridge (`LuckPermsAccess`), and configuration (`ModConfig`). Java 8 compatible across all loaders.
- `versions/<mc>/<loader>`: Thin platform entrypoints, Forge/NeoForge event buses, Fabric Mixins, commands, and loader lifecycle hooks.

## Multi-Version Architecture & Matrix

DimToggle covers every stable Java Edition release from **1.16 through 26.3**, spanning 40 releases and 98 loader targets across Fabric, Forge, and NeoForge:

- **Common Core (`common/src/main/java`)**: Pure Java 8 platform-independent logic. Contains `DimToggleMod`, `DimToggle`, `DimensionLocks`, `AccessPolicy`, `LockDuration`, `LuckPermsAccess`, and `ModConfig`.
- **Target Adapters (`versions/<mc>/<loader>`)**: Dedicated platform entrypoints (`Entrypoint.java`), event listeners (`ForgeDimensionControl`, `NeoForgeDimensionControl`, `FabricDimensionControl`), mixins, and commands.

### Build Tooling

Install Python 3.11+ and JDKs 8, 16, 17, 21, and 25 to build across the complete version matrix. Target-specific compilation selects the appropriate JDK automatically.

```powershell
python tools/kyro/template.py validate
python tools/kyro/template.py core
.\modw.bat '-Pmc=1.16.2' '-Ploader=fabric' build
.\modw.bat '-Pmc=1.20.1' '-Ploader=forge' build
.\modw.bat '-Pmc=1.21.1' '-Ploader=neoforge' build
.\modw.bat '-Pmc=26.3' '-Ploader=fabric' build
```

On Linux/macOS use `sh modw` instead of `.\modw.bat`. Quote the `-P` arguments in PowerShell. With no target flags, the default is Minecraft 1.20.1 Fabric. Use `python tools/kyro/template.py list` for the complete inventory.

`modw` is the version-selecting convenience launcher. The conventional `gradlew` files remain official, checksum-pinned Gradle wrappers for the root dispatcher and require JDK 25 in `JAVA_HOME`. Use `modw` or the Python CLI for target-specific tasks such as `runClient` and `runServer`.

Artifacts are written to `build/<minecraft>/<loader>/libs/`. Distribute the production JAR; do not distribute development or sources JARs. A successful compile is not a gameplay compatibility test.

## Where code belongs

* `common/src/main/java`: shared initialization, configuration, gameplay rules, and narrow platform contracts. This is the default destination for feature work. No Minecraft or loader imports are allowed here. The standalone core build enforces Java 8 API compatibility.
* `common/src/main/resources`: assets and data that are valid on every selected version.
* `versions/<version>/common/src/main`: Minecraft API adaptations shared by that version's loaders. Obfuscated targets use official Mojang mappings where supported; 26.x uses unobfuscated names. Legacy Forge 1.16 retains older class packages even with official member mappings, so namespace-specific imports stay in its loader adapter. Loader-patched APIs and loader integrations also belong in loader-specific adapters.
* `versions/<version>/<loader>/src/main`: loader entrypoints, adapters, metadata, mixins, and version-specific resources.
* `properties/mod.properties`: mod metadata.
* `properties/<minecraft>.properties`: pinned dependency versions, mappings, Java target, and available loaders.
* `build-logic`: centrally maintained build scripts. Version directories contain no build scripts.
* `gradle/profiles.json`: exact Gradle runtime profiles and verified wrapper checksums.

There is one shared source root: `common/`. Add a small platform capability when shared logic needs a Minecraft operation, then implement it in the affected adapters. Do not duplicate gameplay rules across initializers.

Client features belong in a `client` package and must be reached exclusively from loader client initialization. A package is not an isolation mechanism: shared bootstrap code must never reference client classes. The starter contains no client-only code.

The example initializes a JSON configuration and supplies a unit-tested reward policy. It does not register content or subscribe to player events. Those operations need explicit platform capabilities appropriate to the feature.

Older NeoGradle targets fetch client media for client launch and IDE preparation, rather than ordinary compilation and common-logic tests. Pass `-PdownloadAssets=true` to `modw` if a custom test or task needs those assets. Network connections in the build JVM have finite default timeouts.

## Build & Development

Run matrix validation and core unit tests:

```text
python tools/kyro/template.py validate
python tools/kyro/template.py core
```

To build a specific target:
```text
python tools/kyro/template.py gradle "-Pmc=1.20.1" "-Ploader=fabric" build
```

Root shared Java sources use Java 8 syntax and APIs so they can compile for 1.16. Higher-version APIs belong in the selected adapter. Minecraft APIs, rendering, networking, and resource formats change substantially across this range; initializer-only adaptations cannot cover arbitrary features.

## Build isolation

The root scripts load only one Minecraft/loader toolchain per Gradle invocation. Five checksum-pinned wrapper profiles isolate Fabric, ForgeGradle 6, ForgeGradle 7, older NeoForge, and 26.x NeoForge. Fabric's 26.x path uses its unobfuscated plugin; older Fabric releases use remapping. Modern Forge profiles follow the plugin major in the exact official MDK; different patch lines can require different plugin generations. NeoForge before 1.21 uses NeoGradle, while later targets use ModDevGradle. Legacy NeoGradle's source transformer runs on Java 21 independently of the Java 17 game/compiler toolchain.

`buildSrc` is deliberately unnecessary: it would compile inside each selected Gradle runtime and would not solve incompatible plugin versions. Outputs, project caches, and game directories are separated by target. The launcher limits its Windows Gradle process priority; Gradle workers default to two. Adjust worker limits for your machine.

The root Gradle project is a lightweight dispatcher; the authoritative target build is `build-logic/target.gradle`. The launcher copies that build into a generated per-target working directory. This also isolates older Forge plugins that create temporary files outside the configured build directory.

For IDE development, configure a target once with the launcher, then import `.gradle/build-roots/<minecraft>/<loader>` as the Gradle project. Use that profile's Gradle JDK (21 or 25). Its source roots point back to the real `common/` and `versions/` directories. Import one target at a time to avoid overlapping IDE source roots. Importing the repository root provides dispatcher tasks rather than a Minecraft development classpath.

Duplicate Java classes and resource paths fail validation. Resource overlays are not silently merged. Keep version-specific formats out of the universal resource directory. No snapshots, dynamic plugin ranges, automatic dependency updates, or automatic server EULA acceptance are configured.

## Verification and support claims

The initial template baseline was locally build-verified on Windows on 2026-11-02: all 98 catalogued targets passed compilation, common tests, production-JAR metadata/content checks, and Java bytecode target checks. Game launches and gameplay were not exercised. Rebuild after customizing or changing dependencies.

`targets.json` records **availability**, not a support promise. Entries start as `unverified`. Upstream Maven availability alone does not prove a toolchain compiles or launches correctly. Local build reports and CI results provide the evidence for a target. Do not label an entire version family supported based on one representative build.

NeoForge is included from 1.20.2 onward. Where an exact Minecraft release has only a beta NeoForge build, that beta is pinned explicitly rather than silently omitting the target. The historical NeoForge 1.20.1 fork is intentionally omitted in favor of Forge, following NeoForge's recommendation. Other loader families and Minecraft snapshots are outside this template's scope.

The GitHub workflow validates the structure, tests the core, and builds every catalogued loader combination with independent matrix results. It has not run until this repository is hosted and the workflow executes. Before a release, also test the production JAR in a real client and dedicated server for each claimed target; review logs and exercise the actual mod features. Run profiles are available via `runClient` / `runServer` (task names may vary with the loader plugin).

To refresh upstream pins intentionally:

```text
python tools/kyro/catalog.py
python tools/kyro/wrappers.py
python tools/kyro/template.py validate
```

Review all changes and rebuild the matrix afterward. Catalog refresh resets verification statuses. It preserves existing source files and reads the configured package and mod ID for new adapters.

For repeatable local build and JAR verification:

```text
python tools/kyro/verify.py --workers 2
python tools/kyro/verify.py --target 1.20.1/forge --target 26.3/fabric
```

The verifier checks production JAR contents, expanded metadata, and test results, then updates each target's build status. Detailed evidence stays in the sibling `minecraft-mod-template-support/verification` directory. `build-verified` means compilation, tests, and packaging passed; runtime testing is still required.

`python tools/kyro/verify.py --audit-only` rechecks existing artifacts and their test reports without rebuilding. Parallel batches may use separate report directories with `--no-catalog-update`; consolidate them afterward with repeated `--merge-reports <directory>` options. Consolidation validates each report's JAR checksum before updating the inventory.
On Windows the verifier caps the requested parallelism using available memory, budgeting roughly 3 GiB per worker with a 2 GiB reserve. Two workers are the default; up to four are supported. `--resume` skips targets already marked build-verified; use it only when source and build configuration have not changed since those results.

The complete matrix needs substantial disk space for Minecraft dependency preparation. Before starting, the verifier estimates 2 GiB plus 0.5 GiB per uncached target and 0.05 GiB per target with an existing artifact. Set `GRADLE_USER_HOME` to a cache location with sufficient free space. Target project caches live under `.gradle/build-roots`, separately from the source directories. Inventory updates are atomic; `python tools/kyro/catalog.py --recover` can reconstruct the inventory offline from pinned properties and saved evidence if needed.

For a repository-specific cache location, put `gradle.user.home=/absolute/cache/path` in ignored `local.properties`. This overrides `GRADLE_USER_HOME` for this template's launcher and verifier without changing other projects.
You can also set `java.8.home`, `java.16.home`, `java.17.home`, `java.21.home`, and `java.25.home` there instead of setting the matching environment variables. Local settings stay out of Git and exports.

## Upstream references

* [Mojang version manifest](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
* [Fabric metadata](https://meta.fabricmc.net/)
* [Fabric Loom documentation](https://docs.fabricmc.net/develop/loom/)
* [ForgeGradle documentation](https://docs.minecraftforge.net/en/fg-6.x/)
* [Forge official MDKs](https://files.minecraftforge.net/)
* [NeoForge ModDevGradle](https://github.com/neoforged/ModDevGradle)
* [NeoGradle](https://github.com/neoforged/NeoGradle)

The MIT license covers DimToggle. Minecraft, loader tooling, and dependencies retain their own licenses.
