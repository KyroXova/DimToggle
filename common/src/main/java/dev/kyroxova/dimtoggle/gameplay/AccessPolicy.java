package dev.kyroxova.dimtoggle.gameplay;

import dev.kyroxova.dimtoggle.config.ModConfig;
import java.util.List;

public final class AccessPolicy {
    public enum Permission { GRANTED, DENIED, UNAVAILABLE }
    private AccessPolicy() { }

    public static boolean mayEnter(
        ModConfig config,
        DimensionLocks locks,
        String dimension,
        long nowMillis,
        String playerUuid,
        String playerName,
        List<String> playerGroups,
        Permission luckPermsPermission,
        boolean operator
    ) {
        return mayEnter(config, locks, dimension, nowMillis, playerUuid, playerName, playerGroups, luckPermsPermission, operator, false);
    }

    public static boolean mayEnter(
        ModConfig config,
        DimensionLocks locks,
        String dimension,
        long nowMillis,
        String playerUuid,
        String playerName,
        List<String> playerGroups,
        Permission luckPermsPermission,
        boolean operator,
        boolean spectator
    ) {
        dimension = DimensionLocks.normalize(dimension);
        if (locks != null && !locks.isLocked(dimension, nowMillis)) return true;
        if (locks == null && !config.restrictedDimensions.contains(dimension)) return true;
        if (spectator && config.allowSpectators) return true;
        if (operator && config.allowOps) return true;
        if (config.hasPass(dimension, playerUuid, playerName, nowMillis)) return true;
        if (config.enableLuckPerms && luckPermsPermission == Permission.GRANTED) return true;
        if (config.isUserAllowed(dimension, playerUuid, playerName)) return true;
        if (config.isGroupAllowed(dimension, playerGroups)) return true;
        return false;
    }

    public static String permissionNode(String dimension) {
        dimension = DimensionLocks.normalize(dimension);
        return "dimtoggle." + dimension.replace(':', '.');
    }

    public static boolean checkCapacity(
        ModConfig config,
        String dimension,
        int currentPlayersInDimension,
        boolean operator
    ) {
        if (operator && config.allowOps) return true;
        Integer limit = config.getLimit(dimension);
        if (limit == null || limit <= 0) return true;
        return currentPlayersInDimension < limit;
    }

    public static boolean checkMinLevel(
        ModConfig config,
        String dimension,
        int playerExperienceLevel,
        boolean operator
    ) {
        if (operator && config.allowOps) return true;
        int required = config.getMinLevel(dimension);
        if (required <= 0) return true;
        return playerExperienceLevel >= required;
    }
}
