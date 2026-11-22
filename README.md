# DimToggle

**DimToggle** is a lightweight, server-friendly dimension access control and locking mod for Minecraft. It allows server administrators and modpack creators to lock, unlock, restrict, and manage access to any vanilla or modded dimension dynamically or on a timer.

---

## ✨ Features

- 🔒 **Dynamic Dimension Locking**: Lock any dimension permanently or for a specific duration (e.g. `2d`, `12h30m`, `45m`).
- ⏰ **Timed Expiry & Announcements**: Automatically unlocks dimensions when the timer expires and broadcasts server-wide chat notifications.
- 👥 **Granular Access Control**:
  - **Operator Bypass**: Configurable (`allowOps`) permission level 2 access.
  - **Player Allowlist**: Grant specific players entry to locked dimensions via commands (`/dimtoggle allow`) or config.
  - **Group Allowlist**: Allowlist player groups via commands (`/dimtoggle allowgroup`), Scoreboard Teams, or LuckPerms groups.
  - **LuckPerms Integration**: Full support for permission nodes (`dimtoggle.bypass`, `dimtoggle.<namespace>.<dimension>`).
- 🛡️ **Safe Enforcement**:
  - Prevents portal traps, void falling, and travel loops by safely relocating unauthorized players to world spawn (`teleportToSpawn`).
  - Configurable rate-limited warning messages to avoid chat spam.
- 🚀 **Convenient Admin Teleport**: Safely teleport players across dimensions using `/dt <player> <dimension>`.
- ⚡ **Universal Compatibility**: Works on dedicated servers as well as single-player worlds across **Fabric**, **Forge**, and **NeoForge**.

---

## 🎮 Supported Versions

DimToggle provides native builds for **Fabric**, **Forge**, and **NeoForge** across modern and legacy Minecraft releases:

| Minecraft Family | Mod Loaders Supported | Environment |
| :--- | :--- | :--- |
| **1.16.x** (1.16.1 – 1.16.5) | Fabric, Forge | Client & Server |
| **1.17.x** (1.17 – 1.17.1) | Fabric, Forge | Client & Server |
| **1.18.x** (1.18 – 1.18.2) | Fabric, Forge | Client & Server |
| **1.19.x** (1.19 – 1.19.4) | Fabric, Forge | Client & Server |
| **1.20.x** (1.20 – 1.20.6) | Fabric, Forge, NeoForge* | Client & Server |
| **1.21.x** (1.21 – 1.21.11) | Fabric, Forge, NeoForge | Client & Server |
| **26.x** (26.1 – 26.3) | Fabric, Forge, NeoForge | Client & Server |

*\*NeoForge support begins on 1.20.2 and above.*

---

## 📜 Commands & Permissions

All administrative commands require permission level 2 (Operators) or the `dimtoggle.admin` permission node.

| Command | Description |
| :--- | :--- |
| `/dimtoggle list` | Display all currently locked dimensions, active timers, and remaining time. |
| `/dimtoggle lock <dimension> [duration]` | Lock a dimension permanently or for a duration (e.g. `1d`, `12h30m`, `45m`). |
| `/dimtoggle unlock <dimension>` | Unlock a dimension for all players. |
| `/dimtoggle enable <dimension>` | Lock alias (adds dimension to restricted list). |
| `/dimtoggle disable <dimension>` | Unlock alias (removes dimension from restricted list). |
| `/dimtoggle allow <dimension> <player>` | Grant an individual player access to a locked dimension. |
| `/dimtoggle disallow <dimension> <player>` | Remove a player from a locked dimension's allowlist. |
| `/dimtoggle allowgroup <dimension> <group>` | Grant a group (LuckPerms or Scoreboard Team) access to a dimension. |
| `/dimtoggle disallowgroup <dimension> <group>` | Remove a group from a dimension's allowlist. |
| `/dimtoggle reload` | Reload the `config/dimtoggle.json` configuration file. |
| `/dt <player> <dimension>` | Safely teleport a player to the target dimension's spawn point. |

### 🔑 Permission Nodes (LuckPerms)

- `dimtoggle.admin` — Full access to all DimToggle commands.
- `dimtoggle.bypass` — Allows entering any locked dimension regardless of restrictions.
- `dimtoggle.<namespace>.<dimension>` — Grants access to a specific dimension (e.g. `dimtoggle.minecraft.the_end`).

---

## ⚙️ Configuration (`config/dimtoggle.json`)

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
      "Alice",
      "Bob"
    ]
  },
  "allowedGroups": {
    "minecraft:the_end": [
      "vip",
      "donator"
    ]
  }
}
```

- **`enableLuckPerms`**: Enables LuckPerms permission checking if LuckPerms is installed.
- **`teleportToSpawn`**: When `true`, players attempting to enter an unauthorized dimension are safely relocated to world spawn.
- **`allowOps`**: When `true`, server operators (level 2+) bypass dimension locks.
- **`restrictedDimensions`**: Initial list of locked dimensions for newly created worlds.
- **`allowedUsers`**: Map of dimension identifiers to lists of explicitly allowed player names.
- **`allowedGroups`**: Map of dimension identifiers to lists of explicitly allowed group/team names.

---

## 📄 License

DimToggle is released under the MIT License.
