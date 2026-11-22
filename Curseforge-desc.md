# DimToggle

**DimToggle** is a server and modpack utility that allows administrators to dynamically lock, unlock, restrict, and manage player access to any Minecraft dimension (vanilla or modded).

Supports **Fabric**, **Forge**, and **NeoForge** across modern Minecraft releases!

---

## Features

- 🔒 **Dynamic Dimension Locking**: Lock any dimension permanently or for a specific duration (e.g. `2d`, `12h30m`, `45m`).
- ⏳ **Timed Expiry & Announcements**: Automatically unlocks dimensions when the timer expires and broadcasts server-wide notifications.
- 👥 **Granular Access Control**:
  - **Operator Bypass**: Configurable (`allowOps`) permission level 2 access.
  - **Specific Users**: Allowlist individual players via commands (`/dimtoggle allow`) or configuration.
  - **Specific Groups**: Allowlist player groups via commands (`/dimtoggle allowgroup`), LuckPerms groups, or Minecraft Scoreboard Teams.
  - **LuckPerms Integration**: Full integration supporting permission nodes (`dimtoggle.<namespace>.<dimension>`, `dimtoggle.*`, `dimtoggle.bypass`).
- 🛡️ **Safe Enforcement**: Blocks unauthorized travel, provides rate-limited notification messages, and safely relocates players to avoid portal trap loops or void falls.
- 🚀 **Convenient Teleport**: Safe dimension teleportation command (`/dt <player> <dimension>`).

---

## Commands

| Command | Description |
| --- | --- |
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
