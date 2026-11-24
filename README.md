# DimToggle

**DimToggle** is a lightweight, server-side dimension access control and locking mod for Minecraft. It allows server administrators and modpack creators to lock, unlock, restrict, and manage access to any vanilla or modded dimension dynamically or on a timer.

---

## Features

- **Dynamic Dimension Locking**: Lock any dimension permanently or for a specific duration (e.g. `2d`, `12h30m`, `45m`).
- **Timed Expiry and Announcements**: Automatically unlocks dimensions when the timer expires and broadcasts server-wide chat notifications.
- **Granular Access Control**:
  - **Operator Bypass**: Configurable (`allowOps`) permission level 2 access.
  - **Player Allowlist**: Grant specific players entry to locked dimensions via commands (`/dimtoggle allow`) or config.
  - **Group Allowlist**: Allowlist player groups via commands (`/dimtoggle allowgroup`), Scoreboard Teams, or LuckPerms groups.
  - **LuckPerms Integration**: Full support for permission nodes (`dimtoggle.bypass`, `dimtoggle.<namespace>.<dimension>`).
- **Safe Enforcement**:
  - Prevents portal traps, void falling, and travel loops by safely relocating unauthorized players to world spawn (`teleportToSpawn`).
  - Configurable rate-limited warning messages to avoid chat spam.
- **Admin Teleport Utility**: Safely teleport players across dimensions using `/dt <player> <dimension>`.
- **Server-Side Only**: Runs entirely on the server (dedicated server or internal server in singleplayer/LAN). Connecting players do not need the mod installed.

---

## Commands & Permissions

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

### Permission Nodes (LuckPerms)

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
      "Alice",
      "Bob"
    ]
  },
  "allowedGroups": {
    "minecraft:the_end": [
      "vip",
      "donator"
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

## Releases

| Release | Status | Minecraft Compatibility | Target Builds | Changelog | Direct Downloads |
|:---:|:---:|:---:|:---:|:---:|:---:|
| [**v2.0.0**](https://github.com/KyroXova/DimToggle/releases/tag/v2.0.0) | Production (Latest) | 1.16 - 26.3 (40 versions) | 98 Targets | [changelog_1.0.0_to_2.0.0.md](changelogs/changelog_1.0.0_to_2.0.0.md) | [98 Asset JARs](https://github.com/KyroXova/DimToggle/releases/tag/v2.0.0) |

---

## Supported Versions & Downloads

*All builds are server-side; clients do not require installation.*

| Minecraft Version | Forge | Fabric | NeoForge |
|:---:|:---:|:---:|:---:|
| **1.16** | — | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774163) | — |
| **1.16.1** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.1-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774166) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.1-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774165) | — |
| **1.16.2** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.2-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774168) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.2-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774167) | — |
| **1.16.3** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.3-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774170) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.3-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774169) | — |
| **1.16.4** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.4-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774172) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.4-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774171) | — |
| **1.16.5** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.5-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774175) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.16.5-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774174) | — |
| **1.17** | — | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.17-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774176) | — |
| **1.17.1** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.17.1-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774178) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.17.1-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774177) | — |
| **1.18** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.18-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774181) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.18-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774180) | — |
| **1.18.1** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.18.1-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774183) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.18.1-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774182) | — |
| **1.18.2** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.18.2-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774185) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.18.2-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774184) | — |
| **1.19** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774187) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774186) | — |
| **1.19.1** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19.1-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774190) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19.1-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774189) | — |
| **1.19.2** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19.2-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774192) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19.2-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774191) | — |
| **1.19.3** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19.3-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774194) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19.3-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774193) | — |
| **1.19.4** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19.4-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774196) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.19.4-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774195) | — |
| **1.20** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774202) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774199) | — |
| **1.20.1** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.1-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774204) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.1-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774203) | — |
| **1.20.2** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.2-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774206) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.2-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774205) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.2-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774207) |
| **1.20.3** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.3-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774210) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.3-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774209) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.3-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774211) |
| **1.20.4** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.4-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774213) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.4-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774212) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.4-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774214) |
| **1.20.5** | — | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.5-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774215) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.5-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774218) |
| **1.20.6** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.6-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774220) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.6-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774219) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.20.6-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774221) |
| **1.21** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774223) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774222) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774224) |
| **1.21.1** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.1-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774226) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.1-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774225) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.1-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774227) |
| **1.21.2** | — | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.2-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774234) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.2-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774236) |
| **1.21.3** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.3-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774238) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.3-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774237) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.3-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774240) |
| **1.21.4** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.4-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774243) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.4-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774241) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.4-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774244) |
| **1.21.5** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.5-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774246) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.5-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774245) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.5-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774247) |
| **1.21.6** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.6-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774249) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.6-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774248) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.6-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774250) |
| **1.21.7** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.7-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774252) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.7-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774251) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.7-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774253) |
| **1.21.8** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.8-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774255) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.8-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774254) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.8-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774256) |
| **1.21.9** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.9-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774258) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.9-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774257) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.9-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774259) |
| **1.21.10** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.10-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774229) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.10-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774228) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.10-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774230) |
| **1.21.11** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.11-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774232) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.11-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774231) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-1.21.11-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774233) |
| **26.1** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774261) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774260) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774263) |
| **26.1.1** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1.1-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774265) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1.1-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774264) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1.1-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774266) |
| **26.1.2** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1.2-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774268) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1.2-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774267) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.1.2-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774269) |
| **26.2** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.2-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774271) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.2-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774270) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.2-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774272) |
| **26.3** | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.3-forge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774275) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.3-fabric-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774274) | [GitHub](https://github.com/KyroXova/DimToggle/releases/download/v2.0.0/dimtoggle-26.3-neoforge-2.0.0.jar) · [CurseForge](https://www.curseforge.com/minecraft/mc-mods/dimtoggle/files/9774276) |

---

## Authors

DimToggle is developed and maintained by **Kingodogo** and **KyroXova**.

---

## License

DimToggle is released under the MIT License.
