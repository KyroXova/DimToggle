# DimToggle - 1.0.0 → 2.0.0

DimToggle 2.0.0 introduces dynamic timed dimension locks with automatic server notifications, group and player allowlisting, full LuckPerms permission integration, and safe portal relocation to prevent trap loops.

**Full comparison:** [1.0.0...2.0.0](https://github.com/KyroXova/DimToggle/compare/1.0.0...2.0.0)

## Added

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

## Improved

### Commands & Usability

- Added `/dimtoggle enable` and `/dimtoggle disable` command aliases for intuitive quick toggling.
- Enhanced tab completion for all commands, dynamically suggesting dimension identifiers, player names, and durations.
- Added `/dimtoggle reload` command to hot-reload configuration changes from disk without restarting the server.

### Configuration

- Migrated configuration to a clean JSON format (`config/dimtoggle.json`) with organized sections for dimension restrictions, user allowlists, group allowlists, and cooldown intervals.

## Fixed

### Enforcement & Dimension Handling

- Fixed portal desynchronization loops where players entering an unauthorized Nether or End portal would repeatedly trigger travel sounds and screen warps.
- Fixed dimension identifier case-sensitivity issues when checking modded dimensions against the restricted list.
- Prevented unauthorized players from triggering dimension initialization or entity loading when portal access is denied.

## Notes

- DimToggle is a server-side mod. It only needs to be installed on dedicated servers or the host world in singleplayer/LAN; connecting players do not need the mod installed.
- Configuration files from DimToggle 1.0.0 are automatically upgraded to the new format upon first load.
- Dimension permissions are evaluated in priority order: Operators (if enabled) → `dimtoggle.bypass` → Player allowlist → Group allowlist → Dimension-specific permission node.
