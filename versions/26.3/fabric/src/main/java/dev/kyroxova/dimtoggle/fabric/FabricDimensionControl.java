package dev.kyroxova.dimtoggle.fabric;

import dev.kyroxova.dimtoggle.SafeSpawn;
import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy.Permission;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import java.io.IOException;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.logging.Logger;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.storage.LevelResource;

public final class FabricDimensionControl {
    private static final Logger LOG = Logger.getLogger("dimtoggle");
    private static final Map<UUID, Long> LAST_DENIAL = new HashMap<UUID, Long>();
    private static ModConfig config;
    private static DimensionLocks locks;
    private static Path configDir;

    private FabricDimensionControl() { }

    public static void initialize(ModConfig settings, Path cfgDir) {
        config = settings;
        configDir = cfgDir;
    }

    public static boolean mayTravel(ServerPlayer player, String dimension) {
        if (config == null) return true;
        dimension = DimensionLocks.normalize(dimension);
        long now = System.currentTimeMillis();

        if (locks == null) {
            MinecraftServer server = ((ServerLevel) player.level()).getServer();
            if (server != null) {
                try {
                    locks = DimensionLocks.loadOrInitialize(
                        server.getWorldPath(LevelResource.ROOT).resolve("data/dimtoggle-locks.json"),
                        config.restrictedDimensions
                    );
                } catch (IOException ignored) { }
            }
        }
        if (locks == null) return false;

        if (locks.isLocked(dimension, now) && !isPlayerAllowed(player, dimension, now)) {
            deny(player, dimension, now, "§cYou are not allowed to enter " + dimension + "!");
            bounceFromPortal(player);
            return false;
        }

        if (!checkPlayerCapacity(player, dimension)) {
            deny(player, dimension, now, "§cDimension " + dimension + " is full! (" + config.getLimit(dimension) + " players max)");
            bounceFromPortal(player);
            return false;
        }

        if (!checkPlayerMinLevel(player, dimension)) {
            deny(player, dimension, now, "§cYou need at least Level " + config.getMinLevel(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return false;
        }

        if (!checkPlayerRequiredItem(player, dimension)) {
            deny(player, dimension, now, "§cYou must possess a " + config.getRequiredItem(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return false;
        }

        consumeRequiredItem(player, dimension);
        return true;
    }

    private static boolean isPlayerAllowed(ServerPlayer player, String dimension, long now) {
        List<String> groups = config.allowedGroups.get(dimension);
        Permission permission = Permission.DENIED;
        if (player.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER)) {
            permission = Permission.GRANTED;
        }

        return AccessPolicy.mayEnter(
            config,
            locks,
            dimension,
            now,
            player.getStringUUID(),
            player.getName().getString(),
            groups,
            permission,
            player.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER),
            player.isSpectator()
        );
    }

    private static boolean checkPlayerCapacity(ServerPlayer player, String dimension) {
        ServerLevel target = ((ServerLevel) player.level()).getServer().getLevel(ResourceKey.create(
            net.minecraft.core.registries.Registries.DIMENSION,
            Identifier.parse(dimension)
        ));
        int count = target != null ? target.players().size() : 0;
        return AccessPolicy.checkCapacity(config, dimension, count, player.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER));
    }

    private static boolean checkPlayerMinLevel(ServerPlayer player, String dimension) {
        return AccessPolicy.checkMinLevel(config, dimension, player.experienceLevel, player.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER));
    }

    private static boolean checkPlayerRequiredItem(ServerPlayer player, String dimension) {
        String requiredItem = config.getRequiredItem(dimension);
        if (requiredItem == null || requiredItem.isEmpty()) return true;
        if (player.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER) && config.allowOps) return true;

        for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
            net.minecraft.world.item.ItemStack stack = player.getInventory().getItem(i);
            if (!stack.isEmpty()) {
                String itemId = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
                if (itemId.equals(requiredItem)) return true;
            }
        }
        return false;
    }

    private static void consumeRequiredItem(ServerPlayer player, String dimension) {
        if (!config.isConsumeItem(dimension)) return;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return;
        if (player.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER) && config.allowOps) return;
        for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
            net.minecraft.world.item.ItemStack stack = player.getInventory().getItem(i);
            if (!stack.isEmpty()) {
                String itemId = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
                if (itemId.equals(req)) {
                    stack.shrink(1);
                    player.sendSystemMessage(Component.literal("§e[DimToggle] Consumed " + req + " for dimension entry."));
                    break;
                }
            }
        }
    }

    private static void bounceFromPortal(ServerPlayer player) {
        ((ServerLevel) player.level()).getServer().execute(() -> {
            if (!player.isAlive()) return;
            double pushX = 0;
            double pushY = 0.35;
            double pushZ = 0;

            BlockPos pos = player.blockPosition();
            BlockState state = ((ServerLevel) player.level()).getBlockState(pos);
            if (!state.is(Blocks.NETHER_PORTAL) && !state.is(Blocks.END_PORTAL)) {
                state = ((ServerLevel) player.level()).getBlockState(pos.below());
            }

            if (state.is(Blocks.NETHER_PORTAL)) {
                Direction.Axis axis = state.hasProperty(BlockStateProperties.HORIZONTAL_AXIS) ?
                    state.getValue(BlockStateProperties.HORIZONTAL_AXIS) : Direction.Axis.X;
                double yawRad = Math.toRadians(player.getYRot());
                if (axis == Direction.Axis.X) {
                    pushZ = -Math.cos(yawRad) >= 0 ? -2.5 : 2.5;
                } else {
                    pushX = Math.sin(yawRad) >= 0 ? 2.5 : -2.5;
                }
            } else {
                double yawRad = Math.toRadians(player.getYRot());
                pushX = Math.sin(yawRad) * 2.5;
                pushZ = -Math.cos(yawRad) * 2.5;
            }

            double targetX = player.getX() + pushX;
            double targetY = player.getY() + pushY;
            double targetZ = player.getZ() + pushZ;

            player.teleportTo(((ServerLevel) player.level()), targetX, targetY, targetZ, java.util.Collections.emptySet(), player.getYRot(), -10.0f, false);
            player.setDeltaMovement(pushX * 0.32, 0.35, pushZ * 0.32);
            player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 45, 3, false, false, true));
            player.playSound(SoundEvents.SHIELD_BLOCK.value(), 1.0f, 0.6f);
            player.playSound(SoundEvents.ENDERMAN_TELEPORT, 0.8f, 0.5f);
            try {
                ((ServerLevel) player.level()).sendParticles(net.minecraft.core.particles.ParticleTypes.PORTAL, player.getX(), player.getY() + 1.0, player.getZ(), 30, 0.5, 0.5, 0.5, 0.1);
                ((ServerLevel) player.level()).sendParticles(net.minecraft.core.particles.ParticleTypes.ENCHANTED_HIT, player.getX(), player.getY() + 1.0, player.getZ(), 20, 0.3, 0.3, 0.3, 0.2);
            } catch (Exception ignored) { }
        });
    }

    private static void safeTeleportToSpawn(ServerPlayer player) {
        ((ServerLevel) player.level()).getServer().execute(() -> {
            if (!player.isAlive()) return;
            ServerLevel spawnLevel = ((ServerLevel) player.level()).getServer().getLevel(Level.OVERWORLD);
            if (spawnLevel != null) {
                if (((ServerLevel) player.level()) != spawnLevel && (locks == null || locks.isLocked("minecraft:overworld", System.currentTimeMillis()))) return;
                BlockPos spawnPos = SafeSpawn.find(spawnLevel);
                if (spawnPos == null) return;
                player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, java.util.Collections.emptySet(), player.getYRot(), player.getXRot(), false);
            }
        });
    }

    private static void deny(ServerPlayer player, String dimension, long now, String message) {
        Long last = LAST_DENIAL.get(player.getUUID());
        if (last == null || now - last > 2000L) {
            LAST_DENIAL.put(player.getUUID(), now);
            String custom = config.getMessage(dimension);
            player.sendSystemMessage(Component.literal(custom != null ? custom : message));
        }
    }
}
