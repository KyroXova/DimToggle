# DimToggle 2.0.1

DimToggle 2.0.1 is a cumulative patch release providing complete, verified server-side dimension access control across all 98 targets (40 Minecraft versions from 1.16 through 26.3 across Fabric, Forge, and NeoForge).

**Full comparison:** [1.0.0...2.0.1](https://github.com/KyroXova/DimToggle/compare/1.0.0...2.0.1)

---

## Important Notice Regarding 2.0.1 Release

During the initial 2.0.0 release cycle, an internal workspace rollback and branch desynchronization occurred during CI infrastructure modernization. As a result, the 2.0.0 build artifacts for select Forge targets (such as Minecraft 1.16) and newer Minecraft releases (such as 1.21.6 through 26.3) were inadvertently packaged using temporary compilation stubs rather than the fully propagated dimension control implementations, leaving those targets non-functional in that initial release.

**DimToggle 2.0.1 rectifies this completely:**
- All 98 targets across 40 Minecraft versions have been fully implemented, synchronized, and compiled with native dimension control handlers.
- Scaffolding stubs have been eliminated; all published JARs now contain the full production runtime (`ForgeDimensionControl`, `FabricDimensionControl`, `SafeSpawn`, `DimensionLocks`, `ModConfig`, and `LuckPermsAccess`).
- Every target build has been verified and passed 100% across all 18 GitHub Actions CI batches.

---

## Changes in 2.0.1 (Patch Fixes & API Modernization)

### Forge & NeoForge Event Modernization
- **Forge 1.16 MCP Mapping Implementation**: Implemented full `ForgeDimensionControl` using 1.16 MCP mappings (`DimensionTravelEvent`, `ServerTickEvent`, `PlayerRespawnEvent`), safety spawn relocation, and LuckPerms bypass hooks.
- **Forge 59+ Tick Listener Migration**: Upgraded `ServerTickEvent` subscription in Forge 1.21.9 through 26.3 to modern Java record events (`TickEvent.ServerTickEvent.Post`) and record accessor `event.server()`, resolving compatibility breaks with Forge 59+.
- **Minecraft 26.3 Entity API Modernization**: Removed deprecated `hurtMarked` flag invocation in portal bouncing logic to support 26.3 entity lifecycle changes.

### Mojang Mapping & Fabric API Alignment
- **Minecraft 1.21.11 Identifier & Permission Migration**: Updated 1.21.11 Fabric, Forge, and NeoForge to adopt Mojang's modern identifier syntax (`Identifier`, `IdentifierArgument`) and modern game permissions (`Permissions.COMMANDS_GAMEMASTER`), replacing legacy `ResourceLocation` and numeric permission levels.
- **Fabric Loom Build Isolation**: Decoupled 1.21.11+ Fabric Loader configurations from legacy Fabric API bundles in Gradle build logic, ensuring clean pure-Mixin execution without library clashes.

---

## Features & Improvements (Cumulative 2.0.0 Release)

### Timed Dimension Locks & Expiry
- Added support for timed dimension locking with human-readable duration strings (e.g. `2d`, `12h30m`, `45m`).
- Added automatic lock expiry handling with server-wide broadcast announcements when a dimension unlocks.
- Added `/dimtoggle list` command displaying all locked dimensions, whether locks are permanent or timed, and exact remaining duration.

### Access Control & Allowlisting
- Added per-dimension player allowlisting commands (`/dimtoggle allow` and `/dimtoggle disallow`) to grant individual players access without requiring full operator privileges.
- Added group-level allowlisting (`/dimtoggle allowgroup` and `/dimtoggle disallowgroup`) supporting LuckPerms permission groups and Minecraft scoreboard teams.
- Added native LuckPerms permission nodes (`dimtoggle.admin`, `dimtoggle.bypass`, and per-dimension `dimtoggle.<namespace>.<dimension>`).
- Added configurable operator bypass toggle (`allowOps`) to customize server admin access rules.

### Safety & Teleportation
- Added safe relocation enforcement (`teleportToSpawn`) to route unauthorized players directly to world spawn, preventing portal trap loops, suffocation, and void falling.
- Added rate-limited unauthorized entry warnings (`notificationCooldownSeconds`) to eliminate chat and title screen spam during repeated portal attempts.
- Added `/dt <player> <dimension>` administrative teleport utility to safely transport players directly to a dimension's spawn coordinates.

### Commands & Usability
- Added `/dimtoggle enable` and `/dimtoggle disable` command aliases for intuitive quick toggling.
- Enhanced tab completion for all commands, dynamically suggesting dimension identifiers, player names, and durations.
- Added `/dimtoggle reload` command to hot-reload configuration changes from disk without restarting the server.

### Configuration
- Migrated configuration to a clean JSON format (`config/dimtoggle.json`) with organized sections for dimension restrictions, user allowlists, group allowlists, and cooldown intervals.

### Enforcement & Dimension Handling
- Fixed portal desynchronization loops where players entering an unauthorized Nether or End portal would repeatedly trigger travel sounds and screen warps.
- Fixed dimension identifier case-sensitivity issues when checking modded dimensions against the restricted list.
- Prevented unauthorized players from triggering dimension initialization or entity loading when portal access is denied.

---

## Notes

- **Server-Side Only**: DimToggle is entirely server-side. It only needs to be installed on dedicated servers or LAN host sessions; connecting players do not need the mod installed.
- **Automatic Configuration Migration**: Configuration files from DimToggle 1.0.0 are automatically upgraded to the new format upon first load.
- **Permission Evaluation Order**: Permissions are evaluated in priority order: Operators (if enabled) → `dimtoggle.bypass` → Player allowlist → Group allowlist → Dimension-specific permission node.
