# DimToggle

**DimToggle** is a lightweight, server-side dimension access control and locking mod for Minecraft. It allows administrators and modpack creators to dynamically lock, unlock, restrict, and manage player access to any vanilla or modded dimension.

---

## Features

- **Dynamic Dimension Locking**: Lock any dimension permanently or for a specific duration (e.g. `2d`, `12h30m`, `45m`).
- **Timed Expiry and Announcements**: Automatically unlocks dimensions when the timer expires and broadcasts server-wide notifications.
- **Granular Access Control**:
  - **Operator Bypass**: Configurable (`allowOps`) permission level 2 access.
  - **Specific Users**: Allowlist individual players via commands (`/dimtoggle allow`) or configuration.
  - **Specific Groups**: Allowlist player groups via commands (`/dimtoggle allowgroup`), LuckPerms groups, or Minecraft Scoreboard Teams.
  - **LuckPerms Integration**: Full integration supporting permission nodes (`dimtoggle.<namespace>.<dimension>`, `dimtoggle.*`, `dimtoggle.bypass`).
- **Safe Enforcement**: Blocks unauthorized travel, provides rate-limited notification messages, and safely relocates players to avoid portal trap loops or void falls.
- **Convenient Teleport**: Safe dimension teleportation command (`/dt <player> <dimension>`).
- **Server-Side Only**: Runs entirely on the server. Clients do not need the mod installed.

---

## Commands

| Command | Description |
| :--- | :--- |
| `/dimtoggle list` | View all currently locked dimensions, their lock durations, and remaining times. |
| `/dimtoggle lock <dimension> [duration]` | Lock a dimension permanently or for a timed duration (e.g., `1d2h`, `30m`). |
| `/dimtoggle unlock <dimension>` | Unlock a dimension for all players. |
| `/dimtoggle enable <dimension>` | Lock alias (adds dimension to restricted list). |
| `/dimtoggle disable <dimension>` | Unlock alias (removes dimension from restricted list). |
| `/dimtoggle allow <dimension> <player>` | Permit a specific player to enter a locked dimension. |
| `/dimtoggle disallow <dimension> <player>` | Remove a player from a dimension's allowlist. |
| `/dimtoggle allowgroup <dimension> <group>` | Permit a specific group (LuckPerms or Scoreboard Team) to enter. |
| `/dimtoggle disallowgroup <dimension> <group>` | Remove a group from a dimension's allowlist. |
| `/dimtoggle reload` | Reload `dimtoggle.json` configuration from disk. |
| `/dt <player> <dimension>` | Safely teleport players to a dimension spawn position. |

---

## Permission Nodes (LuckPerms)

- `dimtoggle.admin`: Full access to all DimToggle commands.
- `dimtoggle.bypass`: Allows entering any locked dimension regardless of restrictions.
- `dimtoggle.<namespace>.<dimension>`: Grants access to a specific dimension (e.g. `dimtoggle.minecraft.the_end`).

---

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
    "minecraft:the_end": [
      "Notch"
    ]
  },
  "allowedGroups": {
    "minecraft:the_end": [
      "vip"
    ]
  },
  "notificationCooldownSeconds": 3
}
```

- **`enableLuckPerms`**: Enables LuckPerms permission checking if LuckPerms is installed.
- **`teleportToSpawn`**: When `true`, players attempting to enter an unauthorized dimension are safely relocated to world spawn.
- **`allowOps`**: When `true`, server operators (level 2+) bypass dimension locks.
- **`restrictedDimensions`**: Initial list of locked dimensions for newly created worlds.
- **`allowedUsers`**: Map of dimension identifiers to lists of explicitly allowed player names.
- **`allowedGroups`**: Map of dimension identifiers to lists of explicitly allowed group/team names.
- **`notificationCooldownSeconds`**: Cooldown interval between warning notifications when unauthorized players attempt entry.

---

## Supported Versions

DimToggle is a server-side mod (clients do not need to install it). Native builds are provided across all supported releases:

| Minecraft Version | Fabric | Forge | NeoForge | Side |
| :--- | :---: | :---: | :---: | :---: |
| **1.16** | ✓ | ✗ | ✗ | Server-side |
| **1.16.1** | ✓ | ✓ | ✗ | Server-side |
| **1.16.2** | ✓ | ✓ | ✗ | Server-side |
| **1.16.3** | ✓ | ✓ | ✗ | Server-side |
| **1.16.4** | ✓ | ✓ | ✗ | Server-side |
| **1.16.5** | ✓ | ✓ | ✗ | Server-side |
| **1.17** | ✓ | ✗ | ✗ | Server-side |
| **1.17.1** | ✓ | ✓ | ✗ | Server-side |
| **1.18** | ✓ | ✓ | ✗ | Server-side |
| **1.18.1** | ✓ | ✓ | ✗ | Server-side |
| **1.18.2** | ✓ | ✓ | ✗ | Server-side |
| **1.19** | ✓ | ✓ | ✗ | Server-side |
| **1.19.1** | ✓ | ✓ | ✗ | Server-side |
| **1.19.2** | ✓ | ✓ | ✗ | Server-side |
| **1.19.3** | ✓ | ✓ | ✗ | Server-side |
| **1.19.4** | ✓ | ✓ | ✗ | Server-side |
| **1.20** | ✓ | ✓ | ✗ | Server-side |
| **1.20.1** | ✓ | ✓ | ✗ | Server-side |
| **1.20.2** | ✓ | ✓ | ✓ | Server-side |
| **1.20.3** | ✓ | ✓ | ✓ | Server-side |
| **1.20.4** | ✓ | ✓ | ✓ | Server-side |
| **1.20.5** | ✓ | ✗ | ✓ | Server-side |
| **1.20.6** | ✓ | ✓ | ✓ | Server-side |
| **1.21** | ✓ | ✓ | ✓ | Server-side |
| **1.21.1** | ✓ | ✓ | ✓ | Server-side |
| **1.21.2** | ✓ | ✗ | ✓ | Server-side |
| **1.21.3** | ✓ | ✓ | ✓ | Server-side |
| **1.21.4** | ✓ | ✓ | ✓ | Server-side |
| **1.21.5** | ✓ | ✓ | ✓ | Server-side |
| **1.21.6** | ✓ | ✓ | ✓ | Server-side |
| **1.21.7** | ✓ | ✓ | ✓ | Server-side |
| **1.21.8** | ✓ | ✓ | ✓ | Server-side |
| **1.21.9** | ✓ | ✓ | ✓ | Server-side |
| **1.21.10** | ✓ | ✓ | ✓ | Server-side |
| **1.21.11** | ✓ | ✓ | ✓ | Server-side |
| **26.1** | ✓ | ✓ | ✓ | Server-side |
| **26.1.1** | ✓ | ✓ | ✓ | Server-side |
| **26.1.2** | ✓ | ✓ | ✓ | Server-side |
| **26.2** | ✓ | ✓ | ✓ | Server-side |
| **26.3** | ✓ | ✓ | ✓ | Server-side |

---

## Authors

DimToggle is developed and maintained by **Kingodogo** and **KyroXova**.
