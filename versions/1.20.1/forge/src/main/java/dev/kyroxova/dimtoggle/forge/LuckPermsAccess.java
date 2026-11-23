package dev.kyroxova.dimtoggle.forge;

import dev.kyroxova.dimtoggle.gameplay.AccessPolicy.Permission;
import net.minecraft.server.level.ServerPlayer;

final class LuckPermsAccess {
    private LuckPermsAccess() { }

    static Permission check(ServerPlayer player, String node, boolean enabled) {
        return dev.kyroxova.dimtoggle.util.LuckPermsAccess.check(player.getUUID(), node, enabled);
    }
}
