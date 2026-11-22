"""Full-matrix generator and updater for DimToggle across all Minecraft versions and loaders."""
from pathlib import Path
import json

ROOT = Path("E:/Git Repo's/DimToggle")

TARGETS_JSON = json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))
TARGETS_LIST = TARGETS_JSON["targets"]
PUBLISHED_VERSIONS = [t["minecraft"] for t in TARGETS_LIST]

def get_tier(mc: str) -> int:
    if mc.startswith("1.16"): return 1
    if mc.startswith("1.17"): return 2
    if mc.startswith("1.18"): return 3
    if mc.startswith("1.19") or mc in ["1.20", "1.20.1", "1.20.2", "1.20.3", "1.20.4"]: return 4
    return 5

def is_212_or_later(mc: str) -> bool:
    if mc.startswith("26."): return True
    if mc.startswith("1.21."):
        try:
            return int(mc.split(".")[2]) >= 2
        except ValueError:
            return True
    return False

def is_210_or_later(mc: str) -> bool:
    return mc.startswith("26.") or mc.startswith("1.21")

def is_205_or_later(mc: str) -> bool:
    if mc.startswith("26.") or mc.startswith("1.21"): return True
    if mc in ["1.20.5", "1.20.6"]: return True
    return False

def is_206_or_later(mc: str) -> bool:
    return is_205_or_later(mc)

def get_pack_format(mc: str) -> tuple:
    if mc.startswith("1.16.0") or mc in ["1.16", "1.16.1"]: return (5, 5)
    if mc.startswith("1.16"): return (6, 6)
    if mc.startswith("1.17"): return (7, 7)
    if mc.startswith("1.18"): return (8, 9)
    if mc in ["1.19", "1.19.1", "1.19.2"]: return (9, 10)
    if mc == "1.19.3": return (12, 10)
    if mc == "1.19.4": return (13, 12)
    if mc in ["1.20", "1.20.1"]: return (15, 15)
    if mc == "1.20.2": return (18, 18)
    if mc in ["1.20.3", "1.20.4"]: return (22, 26)
    if mc in ["1.20.5", "1.20.6"]: return (32, 41)
    if mc in ["1.21", "1.21.1"]: return (34, 48)
    if mc in ["1.21.2", "1.21.3"]: return (42, 57)
    return (46, 61)

def generate_pack_mcmeta(mc: str) -> str:
    res, data = get_pack_format(mc)
    return f'''{{
  "pack": {{
    "description": "DimToggle resources",
    "pack_format": {res},
    "forge:resource_pack_format": {res},
    "forge:data_pack_format": {data}
  }}
}}
'''

def generate_safespawn(mc: str) -> str:
    if mc.startswith("26."):
        return ""
    tier = get_tier(mc)
    is_212 = is_212_or_later(mc)
    
    if tier <= 2:
        # 1.16 - 1.17
        floor_check = "floor.getMaterial().isSolid()"
        min_y = "0"
        max_y = "256"
    elif tier <= 3 or mc.startswith("1.19"):
        # 1.18 - 1.19
        floor_check = "floor.getMaterial().isSolid()"
        min_y = "level.getMinBuildHeight()"
        max_y = "level.getMaxBuildHeight()"
    elif is_212:
        # 1.21.2+
        floor_check = "floor.isSolid()"
        min_y = "level.getMinY()"
        max_y = "level.getMaxY()"
    else:
        # 1.20.0 - 1.21.1
        floor_check = "floor.isSolid()"
        min_y = "level.getMinBuildHeight()"
        max_y = "level.getMaxBuildHeight()"

    return f"""package dev.kyroxova.dimtoggle;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

public final class SafeSpawn {{
    private SafeSpawn() {{ }}

    public static BlockPos find(ServerLevel level) {{
        BlockPos shared = level.getSharedSpawnPos();
        int minBuild = {min_y};
        int maxBuild = {max_y};
        for (int r = 0; r <= 8; r++) {{
            for (int dx = -r; dx <= r; dx++) {{
                for (int dz = -r; dz <= r; dz++) {{
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != r) continue;
                    int x = shared.getX() + dx;
                    int z = shared.getZ() + dz;
                    for (int y = maxBuild - 2; y >= minBuild + 1; y--) {{
                        BlockPos pos = new BlockPos(x, y, z);
                        BlockState floor = level.getBlockState(pos.below());
                        BlockState feet = level.getBlockState(pos);
                        BlockState head = level.getBlockState(pos.above());
                        if ({floor_check} && feet.isAir() && head.isAir()) {{
                            return pos;
                        }}
                    }}
                }}
            }}
        }}
        return shared;
    }}
}}
"""

def generate_legacy_migration(mc: str, loader: str = "forge") -> str:
    return f"""package dev.kyroxova.dimtoggle.{loader};

import com.electronwill.nightconfig.core.CommentedConfig;
import com.electronwill.nightconfig.toml.TomlParser;
import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

final class LegacyConfigMigration {{
    private LegacyConfigMigration() {{ }}

    static void migrate(Path directory) {{
        Path oldFile = directory.resolve("dimtoggle-common.toml");
        if (Files.exists(directory.resolve("dimtoggle.json")) || !Files.isRegularFile(oldFile)) return;
        try (Reader reader = Files.newBufferedReader(oldFile, StandardCharsets.UTF_8)) {{
            CommentedConfig old = new TomlParser().parse(reader);
            Object luckPerms = old.get("enableLuckPerms");
            Object spawn = old.get("teleportToSpawn");
            Object dimensions = old.get("restrictedDimensions");
            if (!(luckPerms instanceof Boolean) || !(spawn instanceof Boolean) || !(dimensions instanceof List<?>))
                throw new IOException("Missing or invalid legacy settings");
            ModConfig config = new ModConfig();
            config.enableLuckPerms = (Boolean) luckPerms;
            config.teleportToSpawn = (Boolean) spawn;
            config.restrictedDimensions = new ArrayList<String>();
            for (Object dimension : (List<?>) dimensions) {{
                if (!(dimension instanceof String) || !DimensionLocks.validId((String) dimension))
                    throw new IOException("Invalid dimension ID in legacy settings");
                config.restrictedDimensions.add((String) dimension);
            }}
            config.writeNew(directory);
        }} catch (IOException | RuntimeException exception) {{
            throw new IllegalStateException("Could not migrate DimToggle configuration from " + oldFile, exception);
        }}
    }}
}}
"""

def generate_commands_code(send_success_expr, send_failure_expr, broadcast_msg, send_success, send_player_msg, level_getter, is_static: bool = False):
    st = "static " if is_static else ""
    cfg_assign = f"{'config' if is_static else 'this.config'} = ModConfig.load(configDir);"
    p_level = level_getter.replace("player", "p")
    return f"""
    private {st}int list(CommandSourceStack source) {{
        String text = locks.describe(System.currentTimeMillis());
        StringBuilder extra = new StringBuilder();
        extra.append("\\n§eOperators bypass locks: §f").append(config.allowOps);
        extra.append("\\n§eSpectators bypass locks: §f").append(config.allowSpectators);
        if (!config.dimensionLimits.isEmpty()) {{
            extra.append("\\n§6Player Capacity Limits:§f");
            for (Map.Entry<String, Integer> e : config.dimensionLimits.entrySet()) {{
                extra.append("\\n - ").append(e.getKey()).append(": ").append(e.getValue()).append(" max");
            }}
        }}
        if (!config.dimensionMinLevel.isEmpty()) {{
            extra.append("\\n§bXP Level Requirements:§f");
            for (Map.Entry<String, Integer> e : config.dimensionMinLevel.entrySet()) {{
                extra.append("\\n - ").append(e.getKey()).append(": Level ").append(e.getValue());
            }}
        }}
        if (!config.dimensionRequiredItem.isEmpty()) {{
            extra.append("\\n§dRequired Items:§f");
            for (Map.Entry<String, String> e : config.dimensionRequiredItem.entrySet()) {{
                extra.append("\\n - ").append(e.getKey()).append(": ").append(e.getValue());
            }}
        }}
        {send_success_expr("source", '\"§e\" + text + extra.toString()', "false")}
        return 1;
    }}

    private {st}int getAllowOps(CommandSourceStack source) {{
        {send_success_expr("source", '\"§eOperators bypass locks: §f\" + config.allowOps', "false")}
        return 1;
    }}

    private {st}int setAllowOps(CommandSourceStack source, boolean enabled) {{
        try {{
            config.setAllowOps(enabled);
            {send_success_expr("source", '\"§aOperators bypass locks set to: §f\" + enabled', "true")}
            return 1;
        }} catch (IOException e) {{
            {send_failure_expr("source", '\"§cFailed to save configuration: \" + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int setLimit(CommandSourceStack source, String rawDimension, int maxPlayers) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            config.setLimit(dimension, maxPlayers);
            {send_success_expr("source", '"§aSet capacity limit for §f" + dimension + " §ato §f" + maxPlayers + " §aplayers."', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to set limit: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int removeLimit(CommandSourceStack source, String rawDimension) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            config.setLimit(dimension, 0);
            {send_success_expr("source", '"§aRemoved capacity limit for §f" + dimension', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to remove limit: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int setMinLevel(CommandSourceStack source, String rawDimension, int level) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            config.setMinLevel(dimension, level);
            {send_success_expr("source", '"§aRequired experience level for §f" + dimension + " §aset to §f" + level', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to set minimum level: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int setRequiredItem(CommandSourceStack source, String rawDimension, String itemId) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            config.setRequiredItem(dimension, itemId);
            {send_success_expr("source", '"§aRequired item for §f" + dimension + " §aset to §f" + itemId', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to set required item: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int clearRequiredItem(CommandSourceStack source, String rawDimension) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            config.setRequiredItem(dimension, null);
            {send_success_expr("source", '"§aCleared required item for §f" + dimension', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to clear required item: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int unlock(CommandSourceStack source, String rawDimension) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            if (!locks.unlock(dimension)) {{
                {send_failure_expr("source", '"§cDimension is not locked: " + dimension')}
                return 0;
            }}
            {broadcast_msg("source.getServer()", '"§aDimension unlocked: §f" + dimension')}
            return 1;
        }} catch (IOException exception) {{
            {send_failure_expr("source", '"§cCould not persist lock update: " + exception.getMessage()')}
            return 0;
        }}
    }}

    private {st}int lock(CommandSourceStack source, String rawDimension, String duration) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            long expiry = duration == null ? 0 : LockDuration.deadline(duration, System.currentTimeMillis());
            locks.lock(dimension, expiry);
            String message = "§aLocked §f" + dimension + (duration == null ? " §apermanently" : " §afor §f" + duration);
            {send_success_expr("source", "message", "true")}
            ejectUnauthorizedPlayers(source.getServer(), dimension);
            return 1;
        }} catch (IOException | IllegalArgumentException exception) {{
            {send_failure_expr("source", '"§cCould not lock dimension: " + exception.getMessage()')}
            return 0;
        }}
    }}

    private {st}int allowUser(CommandSourceStack source, String rawDimension, String player) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            if (config.allowUser(dimension, player)) {{
                {send_success_expr("source", '"§aAllowed player §f" + player + " §ato enter §f" + dimension', "true")}
                return 1;
            }} else {{
                {send_failure_expr("source", '"§cPlayer §f" + player + " §cis already allowed for §f" + dimension')}
                return 0;
            }}
        }} catch (IOException exception) {{
            {send_failure_expr("source", '"§cCould not save configuration: " + exception.getMessage()')}
            return 0;
        }}
    }}

    private {st}int disallowUser(CommandSourceStack source, String rawDimension, String player) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            if (config.disallowUser(dimension, player)) {{
                {send_success_expr("source", '"§aRemoved player §f" + player + " §afrom §f" + dimension + " §aallowlist"', "true")}
                return 1;
            }} else {{
                {send_failure_expr("source", '"§cPlayer §f" + player + " §cis not in §f" + dimension + " §aallowlist"')}
                return 0;
            }}
        }} catch (IOException exception) {{
            {send_failure_expr("source", '"§cCould not save configuration: " + exception.getMessage()')}
            return 0;
        }}
    }}

    private {st}int allowGroup(CommandSourceStack source, String rawDimension, String group) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            if (config.allowGroup(dimension, group)) {{
                {send_success_expr("source", '"§aAllowed group §f" + group + " §ato enter §f" + dimension', "true")}
                return 1;
            }} else {{
                {send_failure_expr("source", '"§cGroup §f" + group + " §cis already allowed for §f" + dimension')}
                return 0;
            }}
        }} catch (IOException exception) {{
            {send_failure_expr("source", '"§cCould not save configuration: " + exception.getMessage()')}
            return 0;
        }}
    }}

    private {st}int disallowGroup(CommandSourceStack source, String rawDimension, String group) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            if (config.disallowGroup(dimension, group)) {{
                {send_success_expr("source", '"§aRemoved group §f" + group + " §afrom §f" + dimension + " §aallowlist"', "true")}
                return 1;
            }} else {{
                {send_failure_expr("source", '"§cGroup §f" + group + " §cis not in §f" + dimension + " §aallowlist"')}
                return 0;
            }}
        }} catch (IOException exception) {{
            {send_failure_expr("source", '"§cCould not save configuration: " + exception.getMessage()')}
            return 0;
        }}
    }}

    private {st}int info(CommandSourceStack source, String rawDimension) {{
        String dimension = rawDimension == null ? "minecraft:overworld" : DimensionLocks.normalize(rawDimension);
        long now = System.currentTimeMillis();
        boolean locked = locks != null && locks.isLocked(dimension, now);
        Long expiry = locks != null ? locks.snapshot().get(dimension) : null;

        MinecraftServer server = source.getServer();
        int onlineInDim = 0;
        if (server != null) {{
            for (ServerPlayer p : server.getPlayerList().getPlayers()) {{
                String pDim = DimensionLocks.normalize({p_level}.dimension().location().toString());
                if (pDim.equals(dimension)) onlineInDim++;
            }}
        }}

        StringBuilder sb = new StringBuilder();
        sb.append("§6=== [ DimToggle: §f").append(dimension).append(" §6] ===");
        sb.append("\\n§eLock Status: ");
        if (!locked) {{
            sb.append("§aUNLOCKED");
        }} else if (expiry != null && expiry == 0) {{
            sb.append("§cPERMANENTLY LOCKED");
        }} else if (expiry != null) {{
            long rem = Math.max(0, (expiry - now) / 1000L);
            sb.append("§cLOCKED §7(Expires in ").append(rem / 60L).append("m ").append(rem % 60L).append("s)");
        }}

        Integer limit = config.getLimit(dimension);
        sb.append("\\n§eCapacity: §f").append(onlineInDim).append(" / ").append(limit != null && limit > 0 ? limit + " max" : "Unlimited");

        int minLvl = config.getMinLevel(dimension);
        sb.append("\\n§eMin Level: §f").append(minLvl > 0 ? "Level " + minLvl : "None");

        String reqItem = config.getRequiredItem(dimension);
        boolean consume = config.isConsumeItem(dimension);
        sb.append("\\n§eRequired Item: §f").append(reqItem != null ? reqItem + (consume ? " §c(Consumed on entry)" : " §a(Kept)") : "None");

        String customMsg = config.getMessage(dimension);
        if (customMsg != null) {{
            sb.append("\\n§eLock Notice: §f").append(customMsg);
        }}

        List<String> users = config.allowedUsers.get(dimension);
        List<String> groups = config.allowedGroups.get(dimension);
        sb.append("\\n§eWhitelisted: §f").append(users != null ? users.size() : 0).append(" players, ").append(groups != null ? groups.size() : 0).append(" groups");

        Map<String, Long> passes = config.getActivePasses(dimension, now);
        sb.append("\\n§eActive Passes: §f").append(passes.size());
        for (Map.Entry<String, Long> entry : passes.entrySet()) {{
            long rem = Math.max(0, (entry.getValue() - now) / 1000L);
            sb.append("\\n - §a").append(entry.getKey()).append(" §7(").append(rem / 60L).append("m remaining)");
        }}

        String infoText = sb.toString();
        {send_success_expr("source", "infoText", "false")}
        return 1;
    }}

    private {st}int setMessage(CommandSourceStack source, String rawDimension, String message) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            config.setMessage(dimension, message);
            {send_success_expr("source", '"§aSet lockout notice for §f" + dimension + " §ato: §r" + message', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to set notice: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int clearMessage(CommandSourceStack source, String rawDimension) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            config.setMessage(dimension, null);
            {send_success_expr("source", '"§aCleared custom lockout notice for §f" + dimension', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to clear notice: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int addPass(CommandSourceStack source, String rawDimension, String player, String duration) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            long expiry = LockDuration.deadline(duration, System.currentTimeMillis());
            config.addPass(dimension, player, expiry);
            {send_success_expr("source", '"§aGranted §f" + duration + " §aaccess pass for §f" + player + " §ato enter §f" + dimension', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to grant pass: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int revokePass(CommandSourceStack source, String rawDimension, String player) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            if (config.revokePass(dimension, player)) {{
                {send_success_expr("source", '"§aRevoked access pass for §f" + player + " §afrom §f" + dimension', "true")}
                return 1;
            }} else {{
                {send_failure_expr("source", '"§cPlayer §f" + player + " §cdoes not have an active pass for §f" + dimension')}
                return 0;
            }}
        }} catch (IOException e) {{
            {send_failure_expr("source", '"§cFailed to revoke pass: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int getAllowSpectators(CommandSourceStack source) {{
        {send_success_expr("source", '"§eSpectators bypass locks: §f" + config.allowSpectators', "false")}
        return 1;
    }}

    private {st}int setAllowSpectators(CommandSourceStack source, boolean enabled) {{
        try {{
            config.setAllowSpectators(enabled);
            {send_success_expr("source", '"§aSpectators bypass locks set to: §f" + enabled', "true")}
            return 1;
        }} catch (IOException e) {{
            {send_failure_expr("source", '"§cFailed to save configuration: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int setConsumeItem(CommandSourceStack source, String rawDimension, boolean enabled) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        try {{
            config.setConsumeItem(dimension, enabled);
            {send_success_expr("source", '"§aItem consumption for §f" + dimension + " §aset to: §f" + enabled', "true")}
            return 1;
        }} catch (IOException | IllegalArgumentException e) {{
            {send_failure_expr("source", '"§cFailed to set item consumption: " + e.getMessage()')}
            return 0;
        }}
    }}

    private {st}int evict(CommandSourceStack source, String rawDimension, boolean evictAll) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        MinecraftServer server = source.getServer();
        long now = System.currentTimeMillis();
        int count = 0;
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {{
            String currentDim = DimensionLocks.normalize({level_getter}.dimension().location().toString());
            if (currentDim.equals(dimension)) {{
                if (evictAll || !isPlayerAllowed(player, dimension, now)) {{
                    safeTeleportToSpawn(player);
                    {send_player_msg("player", '"§c[DimToggle] You have been evicted from " + dimension + " to spawn."')}
                    count++;
                }}
            }}
        }}
        final int evictedCount = count;
        {send_success_expr("source", '"§aEvicted §f" + evictedCount + " §aplayer(s) from §f" + dimension', "true")}
        return count;
    }}

    private {st}int checkPlayer(CommandSourceStack source, String rawDimension, String playerName) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        MinecraftServer server = source.getServer();
        ServerPlayer targetPlayer = null;
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {{
            if (p.getGameProfile().getName().equalsIgnoreCase(playerName)) {{
                targetPlayer = p;
                break;
            }}
        }}
        if (targetPlayer == null) {{
            {send_failure_expr("source", '"§cPlayer not found online: " + playerName')}
            return 0;
        }}
        long now = System.currentTimeMillis();
        boolean locked = locks != null && locks.isLocked(dimension, now);
        boolean allowed = isPlayerAllowed(targetPlayer, dimension, now);
        boolean capOk = checkPlayerCapacity(targetPlayer, dimension);
        boolean lvlOk = checkPlayerMinLevel(targetPlayer, dimension);
        boolean itemOk = checkPlayerRequiredItem(targetPlayer, dimension);
        boolean pass = config.hasPass(dimension, targetPlayer.getStringUUID(), targetPlayer.getGameProfile().getName(), now);

        StringBuilder sb = new StringBuilder();
        sb.append("§6=== [ DimToggle Access Check: §f").append(playerName).append(" -> ").append(dimension).append(" §6] ===");
        sb.append("\\n§eDimension Locked: §f").append(locked ? "§cYES" : "§aNO");
        sb.append("\\n§eAccess Allowed: §f").append(allowed ? "§aYES" : "§cNO");
        sb.append("\\n§eTemporary Pass: §f").append(pass ? "§aACTIVE" : "§7None");
        sb.append("\\n§eCapacity Check: §f").append(capOk ? "§aPASS" : "§cFULL");
        sb.append("\\n§eLevel Check: §f").append(lvlOk ? "§aPASS" : "§cFAIL (Lvl " + targetPlayer.experienceLevel + " < " + config.getMinLevel(dimension) + ")");
        String req = config.getRequiredItem(dimension);
        if (req != null) {{
            sb.append("\\n§eRequired Item Check: §f").append(itemOk ? "§aPASS" : "§cMISSING (" + req + ")");
        }}
        boolean overall = (!locked || allowed) && capOk && lvlOk && itemOk;
        sb.append("\\n§6Final Verdict: §f").append(overall ? "§a§lALLOWED" : "§c§lDENIED ACCESS");

        String infoText = sb.toString();
        {send_success_expr("source", "infoText", "false")}
        return 1;
    }}

    private {st}int broadcastToDim(CommandSourceStack source, String rawDimension, String message) {{
        String dimension = DimensionLocks.normalize(rawDimension);
        MinecraftServer server = source.getServer();
        int count = 0;
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {{
            String currentDim = DimensionLocks.normalize({level_getter}.dimension().location().toString());
            if (currentDim.equals(dimension)) {{
                {send_player_msg("player", '"§6[" + dimension + "] §f" + message')}
                count++;
            }}
        }}
        final int broadcastCount = count;
        {send_success_expr("source", '"§aBroadcast sent to §f" + broadcastCount + " §aplayer(s) in §f" + dimension', "false")}
        return count;
    }}

    private {st}int reloadConfig(CommandSourceStack source) {{
        try {{
            {cfg_assign}
            {send_success("source", "§aDimToggle configuration reloaded.", "true")}
            return 1;
        }} catch (IOException | RuntimeException exception) {{
            {send_failure_expr("source", '\"§cFailed to reload configuration: \" + exception.getMessage()')}
            return 0;
        }}
    }}
"""

def generate_command_tree():
    return """Commands.literal("dimtoggle").requires(source -> source.hasPermission(2))
                .then(Commands.literal("list").executes(context -> list(context.getSource())))
                .then(Commands.literal("unlock").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .executes(context -> unlock(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString()))))
                .then(Commands.literal("disable").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .executes(context -> unlock(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString()))))
                .then(Commands.literal("enable").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .executes(context -> lock(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), null))))
                .then(Commands.literal("lock").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .executes(context -> lock(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), null))
                    .then(Commands.argument("duration", StringArgumentType.word())
                        .executes(context -> lock(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "duration"))))))
                .then(Commands.literal("allow").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("player", StringArgumentType.word())
                        .executes(context -> allowUser(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "player"))))))
                .then(Commands.literal("disallow").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("player", StringArgumentType.word())
                        .executes(context -> disallowUser(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "player"))))))
                .then(Commands.literal("allowgroup").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("group", StringArgumentType.word())
                        .executes(context -> allowGroup(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "group"))))))
                .then(Commands.literal("disallowgroup").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("group", StringArgumentType.word())
                        .executes(context -> disallowGroup(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "group"))))))
                .then(Commands.literal("allowops")
                    .executes(context -> getAllowOps(context.getSource()))
                    .then(Commands.argument("enabled", BoolArgumentType.bool())
                        .executes(context -> setAllowOps(context.getSource(), BoolArgumentType.getBool(context, "enabled")))))
                .then(Commands.literal("limit").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("max", com.mojang.brigadier.arguments.IntegerArgumentType.integer(1))
                        .executes(context -> setLimit(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(context, "max"))))))
                .then(Commands.literal("unlimit").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .executes(context -> removeLimit(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString()))))
                .then(Commands.literal("minlevel").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("level", com.mojang.brigadier.arguments.IntegerArgumentType.integer(0))
                        .executes(context -> setMinLevel(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(context, "level"))))))
                .then(Commands.literal("requireitem").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("item", StringArgumentType.word())
                        .executes(context -> setRequiredItem(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "item"))))))
                .then(Commands.literal("clearitem").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .executes(context -> clearRequiredItem(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString()))))
                .then(Commands.literal("info")
                    .executes(context -> info(context.getSource(), null))
                    .then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                        .executes(context -> info(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString()))))
                .then(Commands.literal("message").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("text", StringArgumentType.greedyString())
                        .executes(context -> setMessage(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "text"))))))
                .then(Commands.literal("clearmessage").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .executes(context -> clearMessage(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString()))))
                .then(Commands.literal("pass").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("player", StringArgumentType.word())
                        .then(Commands.argument("duration", StringArgumentType.word())
                            .executes(context -> addPass(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "player"), StringArgumentType.getString(context, "duration")))))))
                .then(Commands.literal("revoke").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("player", StringArgumentType.word())
                        .executes(context -> revokePass(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "player"))))))
                .then(Commands.literal("allowspectators")
                    .executes(context -> getAllowSpectators(context.getSource()))
                    .then(Commands.argument("enabled", BoolArgumentType.bool())
                        .executes(context -> setAllowSpectators(context.getSource(), BoolArgumentType.getBool(context, "enabled")))))
                .then(Commands.literal("consumeitem").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("enabled", BoolArgumentType.bool())
                        .executes(context -> setConsumeItem(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), BoolArgumentType.getBool(context, "enabled"))))))
                .then(Commands.literal("evict").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .executes(context -> evict(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), false))
                    .then(Commands.literal("all")
                        .executes(context -> evict(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), true)))))
                .then(Commands.literal("check").then(Commands.argument("player", StringArgumentType.word())
                    .then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                        .executes(context -> checkPlayer(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "player"))))))
                .then(Commands.literal("broadcast").then(Commands.argument("dimension", ResourceLocationArgument.id()).suggests((ctx, b) -> { b.suggest("minecraft:overworld"); b.suggest("minecraft:the_nether"); b.suggest("minecraft:the_end"); return b.buildFuture(); })
                    .then(Commands.argument("message", StringArgumentType.greedyString())
                        .executes(context -> broadcastToDim(context.getSource(), ResourceLocationArgument.getId(context, "dimension").toString(), StringArgumentType.getString(context, "message"))))))
                .then(Commands.literal("reload").executes(context -> reloadConfig(context.getSource())))"""

def generate_forge_control(mc: str) -> str:
    slowness_effect = "MobEffects.SLOWNESS" if is_205_or_later(mc) else "MobEffects.MOVEMENT_SLOWDOWN"
    shield_sound = "SoundEvents.SHIELD_BLOCK.value()" if is_205_or_later(mc) else "SoundEvents.SHIELD_BLOCK"
    teleport_sound = "SoundEvents.ENDERMAN_TELEPORT.value()" if is_205_or_later(mc) else "SoundEvents.ENDERMAN_TELEPORT"
    tier = get_tier(mc)
    is_212 = is_212_or_later(mc)
    inv_getter = "player.inventory" if mc.startswith("1.16") else "player.getInventory()"
    yaw_getter = "player.yRot" if mc.startswith("1.16") else "player.getYRot()"
    pitch_getter = "player.xRot" if mc.startswith("1.16") else "player.getXRot()"

    level_getter = "player.getLevel()" if tier <= 3 or mc.startswith("1.19") else "player.serverLevel()"
    
    if tier <= 3:
        chat_import = "import net.minecraft.network.chat.ChatType;\nimport net.minecraft.network.chat.TextComponent;\nimport net.minecraft.Util;"
        send_success = lambda source, msg, log: f'{source}.sendSuccess(new TextComponent("{msg}"), {log});'
        send_success_expr = lambda source, expr, log: f'{source}.sendSuccess(new TextComponent({expr}), {log});'
        send_failure = lambda source, msg: f'{source}.sendFailure(new TextComponent("{msg}"));'
        send_failure_expr = lambda source, expr: f'{source}.sendFailure(new TextComponent({expr}));'
        send_player_msg = lambda player, expr: f'{player}.sendMessage(new TextComponent({expr}), Util.NIL_UUID);'
        broadcast_msg = lambda server, expr: f'for (ServerPlayer _p : {server}.getPlayerList().getPlayers()) _p.sendMessage(new TextComponent({expr}), Util.NIL_UUID);'
    elif mc.startswith("1.19"):
        chat_import = "import net.minecraft.network.chat.Component;"
        send_success = lambda source, msg, log: f'{source}.sendSuccess(Component.literal("{msg}"), {log});'
        send_success_expr = lambda source, expr, log: f'{source}.sendSuccess(Component.literal({expr}), {log});'
        send_failure = lambda source, msg: f'{source}.sendFailure(Component.literal("{msg}"));'
        send_failure_expr = lambda source, expr: f'{source}.sendFailure(Component.literal({expr}));'
        send_player_msg = lambda player, expr: f'{player}.sendSystemMessage(Component.literal({expr}));'
        broadcast_msg = lambda server, expr: f'for (ServerPlayer _p : {server}.getPlayerList().getPlayers()) _p.sendSystemMessage(Component.literal({expr}));'
    else:
        chat_import = "import net.minecraft.network.chat.Component;"
        send_success = lambda source, msg, log: f'{source}.sendSuccess(() -> Component.literal("{msg}"), {log});'
        send_success_expr = lambda source, expr, log: f'{source}.sendSuccess(() -> Component.literal({expr}), {log});'
        send_failure = lambda source, msg: f'{source}.sendFailure(Component.literal("{msg}"));'
        send_failure_expr = lambda source, expr: f'{source}.sendFailure(Component.literal({expr}));'
        send_player_msg = lambda player, expr: f'{player}.sendSystemMessage(Component.literal({expr}));'
        broadcast_msg = lambda server, expr: f'for (ServerPlayer _p : {server}.getPlayerList().getPlayers()) _p.sendSystemMessage(Component.literal({expr}));'
    if tier <= 2:
        server_starting_import = "import net.minecraftforge.fml.event.server.FMLServerStartingEvent;\\nimport net.minecraftforge.fml.event.server.FMLServerStoppedEvent;"
        server_starting_event = "FMLServerStartingEvent"
        server_stopped_event = "FMLServerStoppedEvent"
        hooks_import = "import net.minecraftforge.fml.server.ServerLifecycleHooks;\\n"
        server_from_tick = "ServerLifecycleHooks.getCurrentServer()"
    elif tier == 3 or mc.startswith("1.19"):
        server_starting_import = "import net.minecraftforge.event.server.ServerStartingEvent;\\nimport net.minecraftforge.event.server.ServerStoppedEvent;"
        server_starting_event = "ServerStartingEvent"
        server_stopped_event = "ServerStoppedEvent"
        hooks_import = "import net.minecraftforge.server.ServerLifecycleHooks;\\n"
        server_from_tick = "ServerLifecycleHooks.getCurrentServer()"
    else:
        server_starting_import = "import net.minecraftforge.event.server.ServerStartingEvent;\\nimport net.minecraftforge.event.server.ServerStoppedEvent;"
        server_starting_event = "ServerStartingEvent"
        server_stopped_event = "ServerStoppedEvent"
        hooks_import = ""
        server_from_tick = "event.getServer()"

    inv_getter = "player.inventory" if mc.startswith("1.16") else "player.getInventory()"
    yaw_getter = "player.yRot" if mc.startswith("1.16") else "player.getYRot()"
    pitch_getter = "player.xRot" if mc.startswith("1.16") else "player.getXRot()"

    if is_212:
        teleport_spawn = f"player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, java.util.Collections.emptySet(), player.getYRot(), player.getXRot(), false);"
        teleport_bounce = f"player.teleportTo(player.serverLevel(), targetX, targetY, targetZ, java.util.Collections.emptySet(), player.getYRot(), -10.0f, false);"
    elif tier <= 3 or mc.startswith("1.19"):
        teleport_spawn = f"player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, {yaw_getter}, {pitch_getter});"
        teleport_bounce = f"player.teleportTo(player.getLevel(), targetX, targetY, targetZ, {yaw_getter}, -10.0f);"
    else:
        teleport_spawn = f"player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, {yaw_getter}, {pitch_getter});"
        teleport_bounce = f"player.teleportTo(player.serverLevel(), targetX, targetY, targetZ, {yaw_getter}, -10.0f);"

    inv_getter = "player.inventory" if mc.startswith("1.16") else "player.getInventory()"
    yaw_getter = "player.yRot" if mc.startswith("1.16") else "player.getYRot()"
    pitch_getter = "player.xRot" if mc.startswith("1.16") else "player.getXRot()"
    dim_registry_ref = "net.minecraft.core.Registry.DIMENSION_REGISTRY" if (tier <= 3 or mc in ["1.19", "1.19.1", "1.19.2"]) else "net.minecraft.core.registries.Registries.DIMENSION"
    res_loc = "ResourceLocation.parse(dimension)" if is_210_or_later(mc) else "new ResourceLocation(dimension)"
    commands_impl = generate_commands_code(send_success_expr, send_failure_expr, broadcast_msg, send_success, send_player_msg, level_getter, is_static=False)
    command_tree = generate_command_tree()
    res_loc = "ResourceLocation.parse(dimension)" if is_210_or_later(mc) else "new ResourceLocation(dimension)"

    return f"""package dev.kyroxova.dimtoggle.forge;

import com.mojang.brigadier.arguments.BoolArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.tree.LiteralCommandNode;
import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.SafeSpawn;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy.Permission;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import dev.kyroxova.dimtoggle.gameplay.LockDuration;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.Set;
import java.util.HashSet;
import java.util.logging.Logger;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.ResourceLocationArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
{chat_import}
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityTravelToDimensionEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
{server_starting_import}
import net.minecraftforge.eventbus.api.SubscribeEvent;
{hooks_import}
public final class ForgeDimensionControl {{
    private static final Logger LOG = Logger.getLogger("dimtoggle");
    private final Path configDir;
    private final Map<UUID, Long> lastDenial = new HashMap<UUID, Long>();
    private ModConfig config;
    private DimensionLocks locks;
    private int ticks;
    private final Set<String> announcedWarnings = new HashSet<String>();

    public ForgeDimensionControl(ModConfig config, Path configDir) {{
        this.config = config;
        this.configDir = configDir;
    }}

    @SubscribeEvent
    public void start(ServerStartingEvent event) {{
        Path path = event.getServer().getWorldPath(LevelResource.ROOT).resolve("data/dimtoggle-locks.json");
        try {{
            locks = DimensionLocks.loadOrInitialize(path, config.restrictedDimensions);
        }} catch (IOException exception) {{
            throw new IllegalStateException("Cannot load DimToggle lock state", exception);
        }}
    }}

    @SubscribeEvent
    public void stop(ServerStoppedEvent event) {{
        locks = null;
        lastDenial.clear();
    }}

    @SubscribeEvent
    public void logout(PlayerEvent.PlayerLoggedOutEvent event) {{
        lastDenial.remove(event.getEntity().getUUID());
    }}

    @SubscribeEvent
    public void login(PlayerEvent.PlayerLoggedInEvent event) {{
        if (event.getEntity() instanceof ServerPlayer) {{
            checkPlayerLocation((ServerPlayer) event.getEntity());
        }}
    }}

    @SubscribeEvent
    public void respawn(PlayerEvent.PlayerRespawnEvent event) {{
        if (event.getEntity() instanceof ServerPlayer) {{
            checkPlayerLocation((ServerPlayer) event.getEntity());
        }}
    }}

    public boolean isPlayerAllowed(ServerPlayer player, String dimension, long now) {{
        dimension = DimensionLocks.normalize(dimension);
        if (locks != null && !locks.isLocked(dimension, now)) return true;
        List<String> groups = new ArrayList<String>();
        if (player.getTeam() != null) {{
            groups.add(player.getTeam().getName());
        }}
        if (config.enableLuckPerms) groups.addAll(dev.kyroxova.dimtoggle.util.LuckPermsAccess.getGroups(player.getUUID()));

        Permission permission = dev.kyroxova.dimtoggle.util.LuckPermsAccess.check(
            player.getUUID(),
            AccessPolicy.permissionNode(dimension),
            config.enableLuckPerms
        );

        return AccessPolicy.mayEnter(
            config,
            locks,
            dimension,
            now,
            player.getStringUUID(),
            player.getGameProfile().getName(),
            groups,
            permission,
            player.hasPermissions(2),
            player.isSpectator()
        );
    }}

    private boolean checkPlayerCapacity(ServerPlayer player, String dimension) {{
        ServerLevel target = player.getServer().getLevel(ResourceKey.create(
            {dim_registry_ref},
            {res_loc}
        ));
        int count = target != null ? target.players().size() : 0;
        return AccessPolicy.checkCapacity(config, dimension, count, player.hasPermissions(2));
    }}

    private boolean checkPlayerMinLevel(ServerPlayer player, String dimension) {{
        return AccessPolicy.checkMinLevel(config, dimension, player.experienceLevel, player.hasPermissions(2));
    }}

    private boolean checkPlayerRequiredItem(ServerPlayer player, String dimension) {{
        if (player.hasPermissions(2) && config.allowOps) return true;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return true;
        for (int i = 0; i < {inv_getter}.getContainerSize(); i++) {{
            net.minecraft.world.item.ItemStack stack = {inv_getter}.getItem(i);
            if (!stack.isEmpty()) {{
                String desc = stack.getItem().getDescriptionId();
                if (desc != null && (desc.contains(req) || stack.getItem().toString().equalsIgnoreCase(req))) return true;
            }}
        }}
        return false;
    }}

    @SubscribeEvent
    public void travel(EntityTravelToDimensionEvent event) {{
        if (!(event.getEntity() instanceof ServerPlayer)) return;
        ServerPlayer player = (ServerPlayer) event.getEntity();
        String dimension = DimensionLocks.normalize(event.getDimension().location().toString());
        if (locks == null) {{
            event.setCanceled(true);
            return;
        }}

        long now = System.currentTimeMillis();

        if (locks.isLocked(dimension, now) && !isPlayerAllowed(player, dimension, now)) {{
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou are not allowed to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }}

        if (!checkPlayerCapacity(player, dimension)) {{
            event.setCanceled(true);
            deny(player, dimension, now, "§cDimension " + dimension + " is full! (" + config.getLimit(dimension) + " players max)");
            bounceFromPortal(player);
            return;
        }}

        if (!checkPlayerMinLevel(player, dimension)) {{
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou need at least Level " + config.getMinLevel(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }}

        if (!checkPlayerRequiredItem(player, dimension)) {{
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou must possess a " + config.getRequiredItem(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }}

        consumeRequiredItem(player, dimension);
    }}

    private void consumeRequiredItem(ServerPlayer player, String dimension) {{
        if (!config.isConsumeItem(dimension)) return;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return;
        if (player.hasPermissions(2) && config.allowOps) return;
        for (int i = 0; i < {inv_getter}.getContainerSize(); i++) {{
            net.minecraft.world.item.ItemStack stack = {inv_getter}.getItem(i);
            if (!stack.isEmpty()) {{
                String desc = stack.getItem().getDescriptionId();
                if (desc != null && (desc.contains(req) || stack.getItem().toString().equalsIgnoreCase(req))) {{
                    stack.shrink(1);
                    {send_player_msg("player", '"§e[DimToggle] Consumed 1x " + req + " for entry into " + dimension + "."')}
                    break;
                }}
            }}
        }}
    }}

    private void deny(ServerPlayer player, String dimension, long now, String message) {{
        Long last = lastDenial.get(player.getUUID());
        if (last == null || now < last || now - last >= 3000) {{
            lastDenial.put(player.getUUID(), now);
            String custom = config.getMessage(dimension);
            String display = custom != null ? "§c[DimToggle] " + custom : message;
            {send_player_msg("player", "display")}
        }}
    }}

    private void bounceFromPortal(ServerPlayer player) {{
        player.getServer().execute(() -> {{
            if (!player.isAlive()) return;
            double pushX = 0;
            double pushY = 0.35;
            double pushZ = 0;

            BlockPos pos = player.blockPosition();
            BlockState state = {level_getter}.getBlockState(pos);
            if (!state.is(Blocks.NETHER_PORTAL) && !state.is(Blocks.END_PORTAL)) {{
                state = {level_getter}.getBlockState(pos.below());
            }}

            if (state.is(Blocks.NETHER_PORTAL)) {{
                Direction.Axis axis = state.hasProperty(BlockStateProperties.HORIZONTAL_AXIS) ?
                    state.getValue(BlockStateProperties.HORIZONTAL_AXIS) : Direction.Axis.X;
                double yawRad = Math.toRadians({yaw_getter});
                if (axis == Direction.Axis.X) {{
                    pushZ = -Math.cos(yawRad) >= 0 ? -2.5 : 2.5;
                }} else {{
                    pushX = Math.sin(yawRad) >= 0 ? 2.5 : -2.5;
                }}
            }} else {{
                double yawRad = Math.toRadians({yaw_getter});
                pushX = Math.sin(yawRad) * 2.5;
                pushZ = -Math.cos(yawRad) * 2.5;
            }}

            double targetX = player.getX() + pushX;
            double targetY = player.getY() + pushY;
            double targetZ = player.getZ() + pushZ;

            {teleport_bounce}
            player.setDeltaMovement(pushX * 0.32, 0.35, pushZ * 0.32);
            player.hurtMarked = true;
            player.addEffect(new MobEffectInstance({slowness_effect}, 45, 3, false, false, true));
            player.playNotifySound({shield_sound}, SoundSource.PLAYERS, 1.0f, 0.6f);
            player.playNotifySound({teleport_sound}, SoundSource.PLAYERS, 0.8f, 0.5f);
            try {{
                {level_getter}.sendParticles(net.minecraft.core.particles.ParticleTypes.PORTAL, player.getX(), player.getY() + 1.0, player.getZ(), 30, 0.5, 0.5, 0.5, 0.1);
                {level_getter}.sendParticles(net.minecraft.core.particles.ParticleTypes.ENCHANTED_HIT, player.getX(), player.getY() + 1.0, player.getZ(), 20, 0.3, 0.3, 0.3, 0.2);
            }} catch (Exception ignored) {{ }}
        }});
    }}

    private void safeTeleportToSpawn(ServerPlayer player) {{
        player.getServer().execute(() -> {{
            if (!player.isAlive()) return;
            ServerLevel spawnLevel = player.getServer().getLevel(Level.OVERWORLD);
            if (spawnLevel != null) {{
                if ({level_getter} != spawnLevel && (locks == null || locks.isLocked("minecraft:overworld", System.currentTimeMillis()))) return;
                BlockPos spawnPos = SafeSpawn.find(spawnLevel);
                if (spawnPos == null) return;
                {teleport_spawn}
            }}
        }});
    }}

    private void checkPlayerLocation(ServerPlayer player) {{
        if (locks == null || player == null || !player.isAlive()) return;
        long now = System.currentTimeMillis();
        String currentDim = DimensionLocks.normalize({level_getter}.dimension().location().toString());
        if (locks.isLocked(currentDim, now) && !isPlayerAllowed(player, currentDim, now)) {{
            safeTeleportToSpawn(player);
            deny(player, currentDim, now, "§cYou are not allowed in " + currentDim + "!");
        }}
    }}

    private void ejectUnauthorizedPlayers(MinecraftServer server, String dimension) {{
        if (server == null || locks == null) return;
        long now = System.currentTimeMillis();
        dimension = DimensionLocks.normalize(dimension);
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {{
            String currentDim = DimensionLocks.normalize({level_getter}.dimension().location().toString());
            if (currentDim.equals(dimension) && !isPlayerAllowed(player, dimension, now)) {{
                safeTeleportToSpawn(player);
                {send_player_msg("player", '\"§cYou have been returned to spawn: \" + dimension + \" is locked!\"')}
            }}
        }}
    }}

    @SubscribeEvent
    public void tick(TickEvent.ServerTickEvent event) {{
        if (event.phase != TickEvent.Phase.END || locks == null || ++ticks % 20 != 0) return;
        MinecraftServer server = {server_from_tick};
        if (server == null) return;
        long now = System.currentTimeMillis();
        try {{
            for (String dimension : locks.expire(now)) {{
                {broadcast_msg("server", '\"§aDimension unlocked: §f\" + dimension')}
            }}
        }} catch (IOException exception) {{
            LOG.severe("Failed to persist expired locks: " + exception.getMessage());
        }}
        for (Map.Entry<String, Long> entry : locks.snapshot().entrySet()) {{
            if (entry.getValue() > now) {{
                long remSec = (entry.getValue() - now) / 1000L;
                if (remSec == 300 || remSec == 60 || remSec == 10) {{
                    String key = entry.getKey() + ":" + remSec;
                    if (announcedWarnings.add(key)) {{
                        String timeStr = remSec >= 60 ? (remSec / 60) + " minutes" : remSec + " seconds";
                        {broadcast_msg("server", '"§6[DimToggle] §fDimension §e" + entry.getKey() + " §fwill unlock in §b" + timeStr + "§f!"')}
                    }}
                }}
            }}
        }}
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {{
            checkPlayerLocation(player);
        }}
    }}

    @SubscribeEvent
    public void commands(RegisterCommandsEvent event) {{
        LiteralCommandNode<CommandSourceStack> dimtoggleNode = event.getDispatcher().register(
            {command_tree}
        );

        event.getDispatcher().register(Commands.literal("dt").requires(source -> source.hasPermission(2)).redirect(dimtoggleNode));
    }}

{commands_impl}
}}
"""

def generate_neoforge_control(mc: str) -> str:
    slowness_effect = "MobEffects.SLOWNESS" if is_205_or_later(mc) else "MobEffects.MOVEMENT_SLOWDOWN"
    shield_sound = "SoundEvents.SHIELD_BLOCK.value()" if is_205_or_later(mc) else "SoundEvents.SHIELD_BLOCK"
    teleport_sound = "SoundEvents.ENDERMAN_TELEPORT.value()" if is_205_or_later(mc) else "SoundEvents.ENDERMAN_TELEPORT"
    is_205_plus = is_205_or_later(mc)
    is_212 = is_212_or_later(mc)
    inv_getter = "player.getInventory()"
    yaw_getter = "player.getYRot()"
    pitch_getter = "player.getXRot()"

    level_getter = "player.serverLevel()"
    send_success_expr = lambda source, expr, log: f'{source}.sendSuccess(() -> Component.literal({expr}), {log});'
    send_failure_expr = lambda source, expr: f'{source}.sendFailure(Component.literal({expr}));'
    send_player_msg = lambda player, expr: f'{player}.sendSystemMessage(Component.literal({expr}));'
    broadcast_msg = lambda server, expr: f'for (ServerPlayer _p : {server}.getPlayerList().getPlayers()) _p.sendSystemMessage(Component.literal({expr}));'
    send_success = lambda source, msg, log: f'{source}.sendSuccess(() -> Component.literal("{msg}"), {log});'

    if is_205_plus:
        tick_import = "import net.neoforged.neoforge.event.tick.ServerTickEvent;"
        tick_method = """    @SubscribeEvent
    public void tick(ServerTickEvent.Post event) {
        if (locks == null || ++ticks % 20 != 0) return;
        MinecraftServer server = event.getServer();
        long now = System.currentTimeMillis();
        try {
            for (String dimension : locks.expire(now)) {
                server.getPlayerList().broadcastSystemMessage(
                    Component.literal("§aDimension unlocked: §f" + dimension), false);
            }
        } catch (IOException exception) {
            LOG.severe("Failed to persist expired locks: " + exception.getMessage());
        }
        for (Map.Entry<String, Long> entry : locks.snapshot().entrySet()) {
            if (entry.getValue() > now) {
                long remSec = (entry.getValue() - now) / 1000L;
                if (remSec == 300 || remSec == 60 || remSec == 10) {
                    String key = entry.getKey() + ":" + remSec;
                    if (announcedWarnings.add(key)) {
                        String timeStr = remSec >= 60 ? (remSec / 60) + " minutes" : remSec + " seconds";
                        server.getPlayerList().broadcastSystemMessage(Component.literal("§6[DimToggle] §fDimension §e" + entry.getKey() + " §fwill unlock in §b" + timeStr + "§f!"), false);
                    }
                }
            }
        }
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            checkPlayerLocation(player);
        }
    }"""
    else:
        tick_import = "import net.neoforged.neoforge.event.TickEvent;\nimport net.neoforged.neoforge.server.ServerLifecycleHooks;"
        tick_method = """    @SubscribeEvent
    public void tick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || locks == null || ++ticks % 20 != 0) return;
        MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
        if (server == null) return;
        long now = System.currentTimeMillis();
        try {
            for (String dimension : locks.expire(now)) {
                server.getPlayerList().broadcastSystemMessage(
                    Component.literal("§aDimension unlocked: §f" + dimension), false);
            }
        } catch (IOException exception) {
            LOG.severe("Failed to persist expired locks: " + exception.getMessage());
        }
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            checkPlayerLocation(player);
        }
    }"""

    if is_212:
        teleport_spawn = f"player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, java.util.Collections.emptySet(), player.getYRot(), player.getXRot(), false);"
        teleport_bounce = f"player.teleportTo(player.serverLevel(), targetX, targetY, targetZ, java.util.Collections.emptySet(), player.getYRot(), -10.0f, false);"
    else:
        teleport_spawn = f"player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, {yaw_getter}, {pitch_getter});"
        teleport_bounce = f"player.teleportTo(player.serverLevel(), targetX, targetY, targetZ, {yaw_getter}, -10.0f);"

    commands_impl = generate_commands_code(send_success_expr, send_failure_expr, broadcast_msg, send_success, send_player_msg, level_getter, is_static=False)
    command_tree = generate_command_tree()
    res_loc = "ResourceLocation.parse(dimension)" if is_210_or_later(mc) else "new ResourceLocation(dimension)"

    return f"""package dev.kyroxova.dimtoggle.neoforge;

import com.mojang.brigadier.arguments.BoolArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.tree.LiteralCommandNode;
import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.SafeSpawn;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy.Permission;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import dev.kyroxova.dimtoggle.gameplay.LockDuration;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.Set;
import java.util.HashSet;
import java.util.logging.Logger;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.ResourceLocationArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
{tick_import}
import net.neoforged.neoforge.event.entity.EntityTravelToDimensionEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.server.ServerStartingEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;

public final class NeoForgeDimensionControl {{
    private static final Logger LOG = Logger.getLogger("dimtoggle");
    private final Path configDir;
    private final Map<UUID, Long> lastDenial = new HashMap<UUID, Long>();
    private ModConfig config;
    private DimensionLocks locks;
    private int ticks;
    private final Set<String> announcedWarnings = new HashSet<String>();

    public NeoForgeDimensionControl(ModConfig config, Path configDir) {{
        this.config = config;
        this.configDir = configDir;
    }}

    @SubscribeEvent
    public void start(ServerStartingEvent event) {{
        Path path = event.getServer().getWorldPath(LevelResource.ROOT).resolve("data/dimtoggle-locks.json");
        try {{
            locks = DimensionLocks.loadOrInitialize(path, config.restrictedDimensions);
        }} catch (IOException exception) {{
            throw new IllegalStateException("Cannot load DimToggle lock state", exception);
        }}
    }}

    @SubscribeEvent
    public void stop(ServerStoppedEvent event) {{
        locks = null;
        lastDenial.clear();
    }}

    @SubscribeEvent
    public void logout(PlayerEvent.PlayerLoggedOutEvent event) {{
        lastDenial.remove(event.getEntity().getUUID());
    }}

    @SubscribeEvent
    public void login(PlayerEvent.PlayerLoggedInEvent event) {{
        if (event.getEntity() instanceof ServerPlayer) {{
            checkPlayerLocation((ServerPlayer) event.getEntity());
        }}
    }}

    @SubscribeEvent
    public void respawn(PlayerEvent.PlayerRespawnEvent event) {{
        if (event.getEntity() instanceof ServerPlayer) {{
            checkPlayerLocation((ServerPlayer) event.getEntity());
        }}
    }}

    public boolean isPlayerAllowed(ServerPlayer player, String dimension, long now) {{
        dimension = DimensionLocks.normalize(dimension);
        if (locks != null && !locks.isLocked(dimension, now)) return true;
        List<String> groups = new ArrayList<String>();
        if (player.getTeam() != null) {{
            groups.add(player.getTeam().getName());
        }}
        if (config.enableLuckPerms) groups.addAll(dev.kyroxova.dimtoggle.util.LuckPermsAccess.getGroups(player.getUUID()));

        Permission permission = dev.kyroxova.dimtoggle.util.LuckPermsAccess.check(
            player.getUUID(),
            AccessPolicy.permissionNode(dimension),
            config.enableLuckPerms
        );

        return AccessPolicy.mayEnter(
            config,
            locks,
            dimension,
            now,
            player.getStringUUID(),
            player.getGameProfile().getName(),
            groups,
            permission,
            player.hasPermissions(2),
            player.isSpectator()
        );
    }}

    private boolean checkPlayerCapacity(ServerPlayer player, String dimension) {{
        ServerLevel target = player.getServer().getLevel(ResourceKey.create(
            net.minecraft.core.registries.Registries.DIMENSION,
            {res_loc}
        ));
        int count = target != null ? target.players().size() : 0;
        return AccessPolicy.checkCapacity(config, dimension, count, player.hasPermissions(2));
    }}

    private boolean checkPlayerMinLevel(ServerPlayer player, String dimension) {{
        return AccessPolicy.checkMinLevel(config, dimension, player.experienceLevel, player.hasPermissions(2));
    }}

    private boolean checkPlayerRequiredItem(ServerPlayer player, String dimension) {{
        if (player.hasPermissions(2) && config.allowOps) return true;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return true;
        for (int i = 0; i < {inv_getter}.getContainerSize(); i++) {{
            net.minecraft.world.item.ItemStack stack = {inv_getter}.getItem(i);
            if (!stack.isEmpty()) {{
                String desc = stack.getItem().getDescriptionId();
                if (desc != null && (desc.contains(req) || stack.getItem().toString().equalsIgnoreCase(req))) return true;
            }}
        }}
        return false;
    }}

    @SubscribeEvent
    public void travel(EntityTravelToDimensionEvent event) {{
        if (!(event.getEntity() instanceof ServerPlayer)) return;
        ServerPlayer player = (ServerPlayer) event.getEntity();
        String dimension = DimensionLocks.normalize(event.getDimension().location().toString());
        if (locks == null) {{
            event.setCanceled(true);
            return;
        }}

        long now = System.currentTimeMillis();

        if (locks.isLocked(dimension, now) && !isPlayerAllowed(player, dimension, now)) {{
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou are not allowed to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }}

        if (!checkPlayerCapacity(player, dimension)) {{
            event.setCanceled(true);
            deny(player, dimension, now, "§cDimension " + dimension + " is full! (" + config.getLimit(dimension) + " players max)");
            bounceFromPortal(player);
            return;
        }}

        if (!checkPlayerMinLevel(player, dimension)) {{
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou need at least Level " + config.getMinLevel(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }}

        if (!checkPlayerRequiredItem(player, dimension)) {{
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou must possess a " + config.getRequiredItem(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }}

        consumeRequiredItem(player, dimension);
    }}

    private void consumeRequiredItem(ServerPlayer player, String dimension) {{
        if (!config.isConsumeItem(dimension)) return;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return;
        if (player.hasPermissions(2) && config.allowOps) return;
        for (int i = 0; i < {inv_getter}.getContainerSize(); i++) {{
            net.minecraft.world.item.ItemStack stack = {inv_getter}.getItem(i);
            if (!stack.isEmpty()) {{
                String desc = stack.getItem().getDescriptionId();
                if (desc != null && (desc.contains(req) || stack.getItem().toString().equalsIgnoreCase(req))) {{
                    stack.shrink(1);
                    {send_player_msg("player", '"§e[DimToggle] Consumed 1x " + req + " for entry into " + dimension + "."')}
                    break;
                }}
            }}
        }}
    }}

    private void deny(ServerPlayer player, String dimension, long now, String message) {{
        Long last = lastDenial.get(player.getUUID());
        if (last == null || now < last || now - last >= 3000) {{
            lastDenial.put(player.getUUID(), now);
            String custom = config.getMessage(dimension);
            String display = custom != null ? "§c[DimToggle] " + custom : message;
            {send_player_msg("player", "display")}
        }}
    }}

    private void bounceFromPortal(ServerPlayer player) {{
        player.getServer().execute(() -> {{
            if (!player.isAlive()) return;
            double pushX = 0;
            double pushY = 0.35;
            double pushZ = 0;

            BlockPos pos = player.blockPosition();
            BlockState state = {level_getter}.getBlockState(pos);
            if (!state.is(Blocks.NETHER_PORTAL) && !state.is(Blocks.END_PORTAL)) {{
                state = {level_getter}.getBlockState(pos.below());
            }}

            if (state.is(Blocks.NETHER_PORTAL)) {{
                Direction.Axis axis = state.hasProperty(BlockStateProperties.HORIZONTAL_AXIS) ?
                    state.getValue(BlockStateProperties.HORIZONTAL_AXIS) : Direction.Axis.X;
                double yawRad = Math.toRadians({yaw_getter});
                if (axis == Direction.Axis.X) {{
                    pushZ = -Math.cos(yawRad) >= 0 ? -2.5 : 2.5;
                }} else {{
                    pushX = Math.sin(yawRad) >= 0 ? 2.5 : -2.5;
                }}
            }} else {{
                double yawRad = Math.toRadians({yaw_getter});
                pushX = Math.sin(yawRad) * 2.5;
                pushZ = -Math.cos(yawRad) * 2.5;
            }}

            double targetX = player.getX() + pushX;
            double targetY = player.getY() + pushY;
            double targetZ = player.getZ() + pushZ;

            {teleport_bounce}
            player.setDeltaMovement(pushX * 0.32, 0.35, pushZ * 0.32);
            player.hurtMarked = true;
            player.addEffect(new MobEffectInstance({slowness_effect}, 45, 3, false, false, true));
            player.playNotifySound({shield_sound}, SoundSource.PLAYERS, 1.0f, 0.6f);
            player.playNotifySound({teleport_sound}, SoundSource.PLAYERS, 0.8f, 0.5f);
            try {{
                {level_getter}.sendParticles(net.minecraft.core.particles.ParticleTypes.PORTAL, player.getX(), player.getY() + 1.0, player.getZ(), 30, 0.5, 0.5, 0.5, 0.1);
                {level_getter}.sendParticles(net.minecraft.core.particles.ParticleTypes.ENCHANTED_HIT, player.getX(), player.getY() + 1.0, player.getZ(), 20, 0.3, 0.3, 0.3, 0.2);
            }} catch (Exception ignored) {{ }}
        }});
    }}

    private void safeTeleportToSpawn(ServerPlayer player) {{
        player.getServer().execute(() -> {{
            if (!player.isAlive()) return;
            ServerLevel spawnLevel = player.getServer().getLevel(Level.OVERWORLD);
            if (spawnLevel != null) {{
                if ({level_getter} != spawnLevel && (locks == null || locks.isLocked("minecraft:overworld", System.currentTimeMillis()))) return;
                BlockPos spawnPos = SafeSpawn.find(spawnLevel);
                if (spawnPos == null) return;
                {teleport_spawn}
            }}
        }});
    }}

    private void checkPlayerLocation(ServerPlayer player) {{
        if (locks == null || player == null || !player.isAlive()) return;
        long now = System.currentTimeMillis();
        String currentDim = DimensionLocks.normalize({level_getter}.dimension().location().toString());
        if (locks.isLocked(currentDim, now) && !isPlayerAllowed(player, currentDim, now)) {{
            safeTeleportToSpawn(player);
            deny(player, currentDim, now, "§cYou are not allowed in " + currentDim + "!");
        }}
    }}

    private void ejectUnauthorizedPlayers(MinecraftServer server, String dimension) {{
        if (server == null || locks == null) return;
        long now = System.currentTimeMillis();
        dimension = DimensionLocks.normalize(dimension);
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {{
            String currentDim = DimensionLocks.normalize({level_getter}.dimension().location().toString());
            if (currentDim.equals(dimension) && !isPlayerAllowed(player, dimension, now)) {{
                safeTeleportToSpawn(player);
                {send_player_msg("player", '\"§cYou have been returned to spawn: \" + dimension + \" is locked!\"')}
            }}
        }}
    }}

{tick_method}

    @SubscribeEvent
    public void commands(RegisterCommandsEvent event) {{
        LiteralCommandNode<CommandSourceStack> dimtoggleNode = event.getDispatcher().register(
            {command_tree}
        );

        event.getDispatcher().register(Commands.literal("dt").requires(source -> source.hasPermission(2)).redirect(dimtoggleNode));
    }}

{commands_impl}
}}
"""

def generate_fabric_control(mc: str) -> str:
    slowness_effect = "MobEffects.SLOWNESS" if is_205_or_later(mc) else "MobEffects.MOVEMENT_SLOWDOWN"
    shield_sound = "SoundEvents.SHIELD_BLOCK.value()" if is_205_or_later(mc) else "SoundEvents.SHIELD_BLOCK"
    teleport_sound = "SoundEvents.ENDERMAN_TELEPORT.value()" if is_205_or_later(mc) else "SoundEvents.ENDERMAN_TELEPORT"
    tier = get_tier(mc)
    is_212 = is_212_or_later(mc)
    inv_getter = "player.inventory" if mc.startswith("1.16") else "player.getInventory()"
    yaw_getter = "player.yRot" if mc.startswith("1.16") else "player.getYRot()"
    pitch_getter = "player.xRot" if mc.startswith("1.16") else "player.getXRot()"

    level_getter = "player.getLevel()" if tier <= 3 or mc.startswith("1.19") else "player.serverLevel()"
    command_callback = "net.fabricmc.fabric.api.command.v1.CommandRegistrationCallback" if tier <= 3 else "net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback"
    command_register_args = "(dispatcher, dedicated) ->" if tier <= 3 else "(dispatcher, registryAccess, environment) ->"

    if tier <= 3:
        chat_import = "import net.minecraft.network.chat.ChatType;\nimport net.minecraft.network.chat.TextComponent;\nimport net.minecraft.Util;"
        send_success = lambda source, msg, log: f'{source}.sendSuccess(new TextComponent("{msg}"), {log});'
        send_success_expr = lambda source, expr, log: f'{source}.sendSuccess(new TextComponent({expr}), {log});'
        send_failure = lambda source, msg: f'{source}.sendFailure(new TextComponent("{msg}"));'
        send_failure_expr = lambda source, expr: f'{source}.sendFailure(new TextComponent({expr}));'
        send_player_msg = lambda player, expr: f'{player}.sendMessage(new TextComponent({expr}), Util.NIL_UUID);'
        broadcast_msg = lambda server, expr: f'for (ServerPlayer _p : {server}.getPlayerList().getPlayers()) _p.sendMessage(new TextComponent({expr}), Util.NIL_UUID);'
    elif mc.startswith("1.19"):
        chat_import = "import net.minecraft.network.chat.Component;"
        send_success = lambda source, msg, log: f'{source}.sendSuccess(Component.literal("{msg}"), {log});'
        send_success_expr = lambda source, expr, log: f'{source}.sendSuccess(Component.literal({expr}), {log});'
        send_failure = lambda source, msg: f'{source}.sendFailure(Component.literal("{msg}"));'
        send_failure_expr = lambda source, expr: f'{source}.sendFailure(Component.literal({expr}));'
        send_player_msg = lambda player, expr: f'{player}.sendSystemMessage(Component.literal({expr}));'
        broadcast_msg = lambda server, expr: f'for (ServerPlayer _p : {server}.getPlayerList().getPlayers()) _p.sendSystemMessage(Component.literal({expr}));'
    else:
        chat_import = "import net.minecraft.network.chat.Component;"
        send_success = lambda source, msg, log: f'{source}.sendSuccess(() -> Component.literal("{msg}"), {log});'
        send_success_expr = lambda source, expr, log: f'{source}.sendSuccess(() -> Component.literal({expr}), {log});'
        send_failure = lambda source, msg: f'{source}.sendFailure(Component.literal("{msg}"));'
        send_failure_expr = lambda source, expr: f'{source}.sendFailure(Component.literal({expr}));'
        send_player_msg = lambda player, expr: f'{player}.sendSystemMessage(Component.literal({expr}));'
        broadcast_msg = lambda server, expr: f'for (ServerPlayer _p : {server}.getPlayerList().getPlayers()) _p.sendSystemMessage(Component.literal({expr}));'

    if is_212:
        teleport_spawn = f"player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, java.util.Collections.emptySet(), player.getYRot(), player.getXRot(), false);"
        teleport_bounce = f"player.teleportTo(player.serverLevel(), targetX, targetY, targetZ, java.util.Collections.emptySet(), player.getYRot(), -10.0f, false);"
    elif tier <= 3 or mc.startswith("1.19"):
        teleport_spawn = f"player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, {yaw_getter}, {pitch_getter});"
        teleport_bounce = f"player.teleportTo(player.getLevel(), targetX, targetY, targetZ, {yaw_getter}, -10.0f);"
    else:
        teleport_spawn = f"player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, {yaw_getter}, {pitch_getter});"
        teleport_bounce = f"player.teleportTo(player.serverLevel(), targetX, targetY, targetZ, {yaw_getter}, -10.0f);"

    commands_impl = generate_commands_code(send_success_expr, send_failure_expr, broadcast_msg, send_success, send_player_msg, level_getter, is_static=True)
    command_tree = generate_command_tree()

    dimension_registry_ref = "net.minecraft.core.Registry.DIMENSION_REGISTRY" if (tier <= 3 or mc in ["1.19", "1.19.1", "1.19.2"]) else "net.minecraft.core.registries.Registries.DIMENSION"
    res_loc = "ResourceLocation.parse(dimension)" if is_210_or_later(mc) else "new ResourceLocation(dimension)"

    return f"""package dev.kyroxova.dimtoggle.fabric;

import com.mojang.brigadier.arguments.BoolArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.tree.LiteralCommandNode;
import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.SafeSpawn;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy.Permission;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import dev.kyroxova.dimtoggle.gameplay.LockDuration;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.Set;
import java.util.HashSet;
import java.util.logging.Logger;
import {command_callback};
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.ResourceLocationArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
{chat_import}
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.storage.LevelResource;

public final class FabricDimensionControl {{
    private static final Logger LOG = Logger.getLogger("dimtoggle");
    private static final Map<UUID, Long> LAST_DENIAL = new HashMap<UUID, Long>();
    private static ModConfig config;
    private static DimensionLocks locks;
    private static Path configDir;
    private static int ticks;
    private static final Set<String> announcedWarnings = new HashSet<String>();

    private FabricDimensionControl() {{ }}

    public static void initialize(ModConfig settings, Path cfgDir) {{
        config = settings;
        configDir = cfgDir;
        ServerLifecycleEvents.SERVER_STARTED.register(server -> {{
            try {{
                locks = DimensionLocks.loadOrInitialize(
                    server.getWorldPath(LevelResource.ROOT).resolve("data/dimtoggle-locks.json"),
                    config.restrictedDimensions
                );
            }} catch (IOException exception) {{
                throw new IllegalStateException("Cannot load DimToggle lock state", exception);
            }}
        }});
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> {{
            locks = null;
            LAST_DENIAL.clear();
        }});
        ServerTickEvents.END_SERVER_TICK.register(FabricDimensionControl::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> LAST_DENIAL.remove(handler.player.getUUID()));
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> checkPlayerLocation(handler.player));

        CommandRegistrationCallback.EVENT.register({command_register_args} {{
            LiteralCommandNode<CommandSourceStack> dimtoggleNode = dispatcher.register(
                {command_tree}
            );

            dispatcher.register(Commands.literal("dt").requires(source -> source.hasPermission(2)).redirect(dimtoggleNode));
        }});
    }}

    public static boolean isPlayerAllowed(ServerPlayer player, String dimension, long now) {{
        dimension = DimensionLocks.normalize(dimension);
        if (locks != null && !locks.isLocked(dimension, now)) return true;
        List<String> groups = new ArrayList<String>();
        if (player.getTeam() != null) {{
            groups.add(player.getTeam().getName());
        }}
        if (config.enableLuckPerms) groups.addAll(dev.kyroxova.dimtoggle.util.LuckPermsAccess.getGroups(player.getUUID()));

        Permission permission = dev.kyroxova.dimtoggle.util.LuckPermsAccess.check(
            player.getUUID(),
            AccessPolicy.permissionNode(dimension),
            config.enableLuckPerms
        );

        return AccessPolicy.mayEnter(
            config,
            locks,
            dimension,
            now,
            player.getStringUUID(),
            player.getGameProfile().getName(),
            groups,
            permission,
            player.hasPermissions(2),
            player.isSpectator()
        );
    }}

    private static boolean checkPlayerCapacity(ServerPlayer player, String dimension) {{
        ServerLevel target = player.getServer().getLevel(ResourceKey.create(
            {dimension_registry_ref},
            {res_loc}
        ));
        int count = target != null ? target.players().size() : 0;
        return AccessPolicy.checkCapacity(config, dimension, count, player.hasPermissions(2));
    }}

    private static boolean checkPlayerMinLevel(ServerPlayer player, String dimension) {{
        return AccessPolicy.checkMinLevel(config, dimension, player.experienceLevel, player.hasPermissions(2));
    }}

    private static boolean checkPlayerRequiredItem(ServerPlayer player, String dimension) {{
        if (player.hasPermissions(2) && config.allowOps) return true;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return true;
        for (int i = 0; i < {inv_getter}.getContainerSize(); i++) {{
            net.minecraft.world.item.ItemStack stack = {inv_getter}.getItem(i);
            if (!stack.isEmpty()) {{
                String desc = stack.getItem().getDescriptionId();
                if (desc != null && (desc.contains(req) || stack.getItem().toString().equalsIgnoreCase(req))) return true;
            }}
        }}
        return false;
    }}

    private static void deny(ServerPlayer player, String dimension, long now, String message) {{
        Long last = LAST_DENIAL.get(player.getUUID());
        if (last == null || now < last || now - last >= 3000) {{
            LAST_DENIAL.put(player.getUUID(), now);
            String custom = config.getMessage(dimension);
            String display = custom != null ? "§c[DimToggle] " + custom : message;
            {send_player_msg("player", "display")}
        }}
    }}

    public static boolean mayTravel(ServerPlayer player, String dimension) {{
        if (locks == null) return false;
        long now = System.currentTimeMillis();
        dimension = DimensionLocks.normalize(dimension);

        if (locks.isLocked(dimension, now) && !isPlayerAllowed(player, dimension, now)) {{
            deny(player, dimension, now, "§cYou are not allowed to enter " + dimension + "!");
            bounceFromPortal(player);
            return false;
        }}

        if (!checkPlayerCapacity(player, dimension)) {{
            deny(player, dimension, now, "§cDimension " + dimension + " is full! (" + config.getLimit(dimension) + " players max)");
            bounceFromPortal(player);
            return false;
        }}

        if (!checkPlayerMinLevel(player, dimension)) {{
            deny(player, dimension, now, "§cYou need at least Level " + config.getMinLevel(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return false;
        }}

        if (!checkPlayerRequiredItem(player, dimension)) {{
            deny(player, dimension, now, "§cYou must possess a " + config.getRequiredItem(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return false;
        }}

        consumeRequiredItem(player, dimension);
        return true;
    }}

    private static void consumeRequiredItem(ServerPlayer player, String dimension) {{
        if (!config.isConsumeItem(dimension)) return;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return;
        if (player.hasPermissions(2) && config.allowOps) return;
        for (int i = 0; i < {inv_getter}.getContainerSize(); i++) {{
            net.minecraft.world.item.ItemStack stack = {inv_getter}.getItem(i);
            if (!stack.isEmpty()) {{
                String desc = stack.getItem().getDescriptionId();
                if (desc != null && (desc.contains(req) || stack.getItem().toString().equalsIgnoreCase(req))) {{
                    stack.shrink(1);
                    {send_player_msg("player", '"§e[DimToggle] Consumed 1x " + req + " for entry into " + dimension + "."')}
                    break;
                }}
            }}
        }}
    }}

    private static void bounceFromPortal(ServerPlayer player) {{
        player.getServer().execute(() -> {{
            if (!player.isAlive()) return;
            double pushX = 0;
            double pushY = 0.35;
            double pushZ = 0;

            BlockPos pos = player.blockPosition();
            BlockState state = {level_getter}.getBlockState(pos);
            if (!state.is(Blocks.NETHER_PORTAL) && !state.is(Blocks.END_PORTAL)) {{
                state = {level_getter}.getBlockState(pos.below());
            }}

            if (state.is(Blocks.NETHER_PORTAL)) {{
                Direction.Axis axis = state.hasProperty(BlockStateProperties.HORIZONTAL_AXIS) ?
                    state.getValue(BlockStateProperties.HORIZONTAL_AXIS) : Direction.Axis.X;
                double yawRad = Math.toRadians({yaw_getter});
                if (axis == Direction.Axis.X) {{
                    pushZ = -Math.cos(yawRad) >= 0 ? -2.5 : 2.5;
                }} else {{
                    pushX = Math.sin(yawRad) >= 0 ? 2.5 : -2.5;
                }}
            }} else {{
                double yawRad = Math.toRadians({yaw_getter});
                pushX = Math.sin(yawRad) * 2.5;
                pushZ = -Math.cos(yawRad) * 2.5;
            }}

            double targetX = player.getX() + pushX;
            double targetY = player.getY() + pushY;
            double targetZ = player.getZ() + pushZ;

            {teleport_bounce}
            player.setDeltaMovement(pushX * 0.32, 0.35, pushZ * 0.32);
            player.hurtMarked = true;
            player.addEffect(new MobEffectInstance({slowness_effect}, 45, 3, false, false, true));
            player.playNotifySound({shield_sound}, SoundSource.PLAYERS, 1.0f, 0.6f);
            player.playNotifySound({teleport_sound}, SoundSource.PLAYERS, 0.8f, 0.5f);
            try {{
                {level_getter}.sendParticles(net.minecraft.core.particles.ParticleTypes.PORTAL, player.getX(), player.getY() + 1.0, player.getZ(), 30, 0.5, 0.5, 0.5, 0.1);
                {level_getter}.sendParticles(net.minecraft.core.particles.ParticleTypes.ENCHANTED_HIT, player.getX(), player.getY() + 1.0, player.getZ(), 20, 0.3, 0.3, 0.3, 0.2);
            }} catch (Exception ignored) {{ }}
        }});
    }}

    private static void safeTeleportToSpawn(ServerPlayer player) {{
        player.getServer().execute(() -> {{
            if (!player.isAlive()) return;
            ServerLevel spawnLevel = player.getServer().getLevel(Level.OVERWORLD);
            if (spawnLevel != null) {{
                if ({level_getter} != spawnLevel && (locks == null || locks.isLocked("minecraft:overworld", System.currentTimeMillis()))) return;
                BlockPos spawnPos = SafeSpawn.find(spawnLevel);
                if (spawnPos == null) return;
                {teleport_spawn}
            }}
        }});
    }}

    private static void checkPlayerLocation(ServerPlayer player) {{
        if (locks == null || player == null || !player.isAlive()) return;
        long now = System.currentTimeMillis();
        String currentDim = DimensionLocks.normalize({level_getter}.dimension().location().toString());
        if (locks.isLocked(currentDim, now) && !isPlayerAllowed(player, currentDim, now)) {{
            safeTeleportToSpawn(player);
            deny(player, currentDim, now, "§cYou are not allowed in " + currentDim + "!");
        }}
    }}

    private static void ejectUnauthorizedPlayers(MinecraftServer server, String dimension) {{
        if (server == null || locks == null) return;
        long now = System.currentTimeMillis();
        dimension = DimensionLocks.normalize(dimension);
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {{
            String currentDim = DimensionLocks.normalize({level_getter}.dimension().location().toString());
            if (currentDim.equals(dimension) && !isPlayerAllowed(player, dimension, now)) {{
                safeTeleportToSpawn(player);
                {send_player_msg("player", '\"§cYou have been returned to spawn: \" + dimension + \" is locked!\"')}
            }}
        }}
    }}

    private static void tick(MinecraftServer server) {{
        if (locks == null || ++ticks % 20 != 0) return;
        long now = System.currentTimeMillis();
        try {{
            for (String dimension : locks.expire(now)) {{
                {broadcast_msg("server", '\"§aDimension unlocked: §f\" + dimension')}
            }}
        }} catch (IOException exception) {{
            LOG.severe("Failed to persist expired locks: " + exception.getMessage());
        }}
        for (Map.Entry<String, Long> entry : locks.snapshot().entrySet()) {{
            if (entry.getValue() > now) {{
                long remSec = (entry.getValue() - now) / 1000L;
                if (remSec == 300 || remSec == 60 || remSec == 10) {{
                    String key = entry.getKey() + ":" + remSec;
                    if (announcedWarnings.add(key)) {{
                        String timeStr = remSec >= 60 ? (remSec / 60) + " minutes" : remSec + " seconds";
                        {broadcast_msg("server", '"§6[DimToggle] §fDimension §e" + entry.getKey() + " §fwill unlock in §b" + timeStr + "§f!"')}
                    }}
                }}
            }}
        }}
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {{
            checkPlayerLocation(player);
        }}
    }}

{commands_impl}
}}
"""

def generate_serverplayer_mixin(mc: str) -> str:
    tier = get_tier(mc)
    is_212 = is_212_or_later(mc)
    is_21 = mc in ["1.21", "1.21.1"]

    level_getter = "player.getLevel()" if tier <= 3 or mc.startswith("1.19") else "player.serverLevel()"

    if is_212:
        return """package dev.kyroxova.dimtoggle.fabric.mixin;

import dev.kyroxova.dimtoggle.fabric.FabricDimensionControl;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.portal.TeleportTransition;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ServerPlayer.class)
public abstract class ServerPlayerMixin {
    @Inject(method = "teleport(Lnet/minecraft/world/level/portal/TeleportTransition;)Lnet/minecraft/server/level/ServerPlayer;", at = @At("HEAD"), cancellable = true)
    private void dimtoggle$beforeTravel(TeleportTransition transition, CallbackInfoReturnable<ServerPlayer> callback) {
        if (transition != null && !FabricDimensionControl.mayTravel((ServerPlayer) (Object) this, transition.newLevel().dimension().location().toString()))
            callback.setReturnValue(null);
    }
}
"""
    elif is_21:
        return """package dev.kyroxova.dimtoggle.fabric.mixin;

import dev.kyroxova.dimtoggle.fabric.FabricDimensionControl;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.portal.DimensionTransition;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ServerPlayer.class)
public abstract class ServerPlayerMixin {
    @Inject(method = "changeDimension", at = @At("HEAD"), cancellable = true)
    private void dimtoggle$beforeTravel(DimensionTransition transition, CallbackInfoReturnable<Entity> callback) {
        if (transition != null && !FabricDimensionControl.mayTravel((ServerPlayer) (Object) this, transition.newLevel().dimension().location().toString()))
            callback.setReturnValue(null);
    }

    @Inject(method = "teleportTo(Lnet/minecraft/server/level/ServerLevel;DDDFF)V", at = @At("HEAD"), cancellable = true)
    private void dimtoggle$beforeTeleport(ServerLevel destination, double x, double y, double z, float yaw, float pitch, CallbackInfo callback) {
        ServerPlayer player = (ServerPlayer) (Object) this;
        if (player.serverLevel() != destination && !FabricDimensionControl.mayTravel(player, destination.dimension().location().toString()))
            callback.cancel();
    }
}
"""
    else:
        return f"""package dev.kyroxova.dimtoggle.fabric.mixin;

import dev.kyroxova.dimtoggle.fabric.FabricDimensionControl;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ServerPlayer.class)
public abstract class ServerPlayerMixin {{
    @Inject(method = "changeDimension", at = @At("HEAD"), cancellable = true)
    private void dimtoggle$beforeTravel(ServerLevel destination, CallbackInfoReturnable<Entity> callback) {{
        if (!FabricDimensionControl.mayTravel((ServerPlayer) (Object) this, destination.dimension().location().toString()))
            callback.setReturnValue(null);
    }}

    @Inject(method = "teleportTo(Lnet/minecraft/server/level/ServerLevel;DDDFF)V", at = @At("HEAD"), cancellable = true)
    private void dimtoggle$beforeTeleport(ServerLevel destination, double x, double y, double z, float yaw, float pitch, CallbackInfo callback) {{
        ServerPlayer player = (ServerPlayer) (Object) this;
        if ({level_getter} != destination && !FabricDimensionControl.mayTravel(player, destination.dimension().location().toString()))
            callback.cancel();
    }}
}}
"""

def generate_fabric_entrypoint(mc: str) -> str:
    return """package dev.kyroxova.dimtoggle.fabric;

import dev.kyroxova.dimtoggle.DimToggleMod;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import dev.kyroxova.dimtoggle.config.ModConfig;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import java.nio.file.Path;

public final class Entrypoint implements ModInitializer {
    public void onInitialize() {
        Path configDir = FabricLoader.getInstance().getConfigDir();
        ModConfig config = DimToggleMod.initialize(new RuntimePlatform("fabric", configDir));
        FabricDimensionControl.initialize(config, configDir);
    }
}
"""

def generate_forge_entrypoint(mc: str) -> str:
    return """package dev.kyroxova.dimtoggle.forge;

import dev.kyroxova.dimtoggle.DimToggleMod;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import dev.kyroxova.dimtoggle.config.ModConfig;
import net.minecraftforge.common.MinecraftForge;
import java.nio.file.Path;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.loading.FMLPaths;

@Mod(DimToggleMod.MOD_ID)
public final class Entrypoint {
    public Entrypoint() {
        Path configDir = FMLPaths.CONFIGDIR.get();
        LegacyConfigMigration.migrate(configDir);
        ModConfig config = DimToggleMod.initialize(new RuntimePlatform("forge", configDir));
        MinecraftForge.EVENT_BUS.register(new ForgeDimensionControl(config, configDir));
    }
}
"""

def generate_neoforge_entrypoint(mc: str) -> str:
    return """package dev.kyroxova.dimtoggle.neoforge;

import dev.kyroxova.dimtoggle.DimToggleMod;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import dev.kyroxova.dimtoggle.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;
import java.nio.file.Path;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLPaths;

@Mod(DimToggleMod.MOD_ID)
public final class Entrypoint {
    public Entrypoint() {
        Path configDir = FMLPaths.CONFIGDIR.get();
        LegacyConfigMigration.migrate(configDir);
        ModConfig config = DimToggleMod.initialize(new RuntimePlatform("neoforge", configDir));
        NeoForge.EVENT_BUS.register(new NeoForgeDimensionControl(config, configDir));
    }
}
"""

def write_if_changed(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")

def apply_all():
    for target in TARGETS_LIST:
        mc = target["minecraft"]
        loaders = target["loaders"].keys()

        if mc.startswith("26."):
            # Future mock version - minimal entrypoints without Minecraft classes
            sp = ROOT / f"versions/{mc}/common/src/main/java/dev/kyroxova/dimtoggle/SafeSpawn.java"
            if sp.exists(): sp.unlink()

            if "fabric" in loaders:
                write_if_changed(ROOT / f"versions/{mc}/fabric/src/main/java/dev/kyroxova/dimtoggle/fabric/Entrypoint.java", generate_fabric_entrypoint(mc))
                fc = ROOT / f"versions/{mc}/fabric/src/main/java/dev/kyroxova/dimtoggle/fabric/FabricDimensionControl.java"
                if fc.exists(): fc.unlink()
                mx = ROOT / f"versions/{mc}/fabric/src/main/java/dev/kyroxova/dimtoggle/fabric/mixin/ServerPlayerMixin.java"
                if mx.exists(): mx.unlink()
                mj = ROOT / f"versions/{mc}/fabric/src/main/resources/dimtoggle.mixins.json"
                if mj.exists(): mj.unlink()
                fmod = ROOT / f"versions/{mc}/fabric/src/main/resources/fabric.mod.json"
                write_if_changed(fmod, f'''{{
  "schemaVersion": 1,
  "id": "${{mod_id}}",
  "version": "${{mod_version}}",
  "name": "${{mod_name}}",
  "description": "${{mod_description}}",
  "license": "${{mod_license}}",
  "environment": "*",
  "entrypoints": {{ "main": ["dev.kyroxova.dimtoggle.fabric.Entrypoint"] }},
  "depends": {{ "fabricloader": ">=${{loader_version}}", "minecraft": "{mc}", "java": ">=${{java_release}}" }}
}}
''')
                write_if_changed(ROOT / f"versions/{mc}/fabric/src/main/resources/pack.mcmeta", generate_pack_mcmeta(mc))

            if "forge" in loaders:
                write_if_changed(ROOT / f"versions/{mc}/forge/src/main/java/dev/kyroxova/dimtoggle/forge/Entrypoint.java", generate_forge_entrypoint(mc))
                write_if_changed(ROOT / f"versions/{mc}/forge/src/main/java/dev/kyroxova/dimtoggle/forge/LegacyConfigMigration.java", generate_legacy_migration(mc, "forge"))
                fc = ROOT / f"versions/{mc}/forge/src/main/java/dev/kyroxova/dimtoggle/forge/ForgeDimensionControl.java"
                if fc.exists(): fc.unlink()
                write_if_changed(ROOT / f"versions/{mc}/forge/src/main/resources/pack.mcmeta", generate_pack_mcmeta(mc))

            if "neoforge" in loaders:
                write_if_changed(ROOT / f"versions/{mc}/neoforge/src/main/java/dev/kyroxova/dimtoggle/neoforge/Entrypoint.java", generate_neoforge_entrypoint(mc))
                write_if_changed(ROOT / f"versions/{mc}/neoforge/src/main/java/dev/kyroxova/dimtoggle/neoforge/LegacyConfigMigration.java", generate_legacy_migration(mc, "neoforge"))
                fc = ROOT / f"versions/{mc}/neoforge/src/main/java/dev/kyroxova/dimtoggle/neoforge/NeoForgeDimensionControl.java"
                if fc.exists(): fc.unlink()
                write_if_changed(ROOT / f"versions/{mc}/neoforge/src/main/resources/pack.mcmeta", generate_pack_mcmeta(mc))
            continue

        # Real Minecraft targets
        if mc in ["1.16.1", "1.16.2", "1.16.3", "1.16.4"]:
            sp_common = ROOT / f"versions/{mc}/common/src/main/java/dev/kyroxova/dimtoggle/SafeSpawn.java"
            if sp_common.exists(): sp_common.unlink()
            write_if_changed(ROOT / f"versions/{mc}/fabric/src/main/java/dev/kyroxova/dimtoggle/SafeSpawn.java", generate_safespawn(mc))
        else:
            write_if_changed(ROOT / f"versions/{mc}/common/src/main/java/dev/kyroxova/dimtoggle/SafeSpawn.java", generate_safespawn(mc))

        # Fabric
        if "fabric" in loaders:
            write_if_changed(ROOT / f"versions/{mc}/fabric/src/main/java/dev/kyroxova/dimtoggle/fabric/FabricDimensionControl.java", generate_fabric_control(mc))
            write_if_changed(ROOT / f"versions/{mc}/fabric/src/main/java/dev/kyroxova/dimtoggle/fabric/Entrypoint.java", generate_fabric_entrypoint(mc))
            write_if_changed(ROOT / f"versions/{mc}/fabric/src/main/java/dev/kyroxova/dimtoggle/fabric/mixin/ServerPlayerMixin.java", generate_serverplayer_mixin(mc))
            
            compat = "JAVA_8" if get_tier(mc) == 1 else ("JAVA_16" if get_tier(mc) == 2 else ("JAVA_17" if get_tier(mc) <= 4 else "JAVA_21"))
            mixin_json = ROOT / f"versions/{mc}/fabric/src/main/resources/dimtoggle.mixins.json"
            write_if_changed(mixin_json, f'''{{
  "required": true,
  "minVersion": "0.8",
  "package": "dev.kyroxova.dimtoggle.fabric.mixin",
  "compatibilityLevel": "{compat}",
  "mixins": [
    "ServerPlayerMixin"
  ],
  "injectors": {{
    "defaultRequire": 1
  }}
}}
''')
            fmod = ROOT / f"versions/{mc}/fabric/src/main/resources/fabric.mod.json"
            write_if_changed(fmod, f'''{{
  "schemaVersion": 1,
  "id": "${{mod_id}}",
  "version": "${{mod_version}}",
  "name": "${{mod_name}}",
  "description": "${{mod_description}}",
  "license": "${{mod_license}}",
  "environment": "*",
  "entrypoints": {{
    "main": [
      "dev.kyroxova.dimtoggle.fabric.Entrypoint"
    ]
  }},
  "mixins": [
    "dimtoggle.mixins.json"
  ],
  "depends": {{
    "fabricloader": ">=${{loader_version}}",
    "minecraft": "{mc}"
  }}
}}
''')
            write_if_changed(ROOT / f"versions/{mc}/fabric/src/main/resources/pack.mcmeta", generate_pack_mcmeta(mc))

        # Forge
        if "forge" in loaders:
            forge_dir = ROOT / f"versions/{mc}/forge"
            if mc in ["1.16.1", "1.16.2", "1.16.3", "1.16.4"]:
                # Early Forge before official Mojmap support
                write_if_changed(forge_dir / "src/main/java/dev/kyroxova/dimtoggle/forge/Entrypoint.java", generate_forge_entrypoint(mc))
                write_if_changed(forge_dir / "src/main/java/dev/kyroxova/dimtoggle/forge/LegacyConfigMigration.java", generate_legacy_migration(mc, "forge"))
                fc = forge_dir / "src/main/java/dev/kyroxova/dimtoggle/forge/ForgeDimensionControl.java"
                if fc.exists(): fc.unlink()
            else:
                write_if_changed(forge_dir / "src/main/java/dev/kyroxova/dimtoggle/forge/ForgeDimensionControl.java", generate_forge_control(mc))
                write_if_changed(forge_dir / "src/main/java/dev/kyroxova/dimtoggle/forge/Entrypoint.java", generate_forge_entrypoint(mc))
                write_if_changed(forge_dir / "src/main/java/dev/kyroxova/dimtoggle/forge/LegacyConfigMigration.java", generate_legacy_migration(mc, "forge"))
            write_if_changed(forge_dir / "src/main/resources/pack.mcmeta", generate_pack_mcmeta(mc))

        # NeoForge
        if "neoforge" in loaders:
            neoforge_dir = ROOT / f"versions/{mc}/neoforge"
            write_if_changed(neoforge_dir / "src/main/java/dev/kyroxova/dimtoggle/neoforge/NeoForgeDimensionControl.java", generate_neoforge_control(mc))
            write_if_changed(neoforge_dir / "src/main/java/dev/kyroxova/dimtoggle/neoforge/Entrypoint.java", generate_neoforge_entrypoint(mc))
            write_if_changed(neoforge_dir / "src/main/java/dev/kyroxova/dimtoggle/neoforge/LegacyConfigMigration.java", generate_legacy_migration(mc, "neoforge"))
            write_if_changed(neoforge_dir / "src/main/resources/pack.mcmeta", generate_pack_mcmeta(mc))

if __name__ == "__main__":
    apply_all()
    print("Full matrix generated and updated successfully across all 40 published versions.")
