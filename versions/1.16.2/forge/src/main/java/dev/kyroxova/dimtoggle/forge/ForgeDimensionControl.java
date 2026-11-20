package dev.kyroxova.dimtoggle.forge;

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
import net.minecraft.network.chat.ChatType;
import net.minecraft.network.chat.TextComponent;
import net.minecraft.Util;
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
import net.minecraftforge.event.server.ServerStartingEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.server.ServerLifecycleHooks;

public final class ForgeDimensionControl {
    private static final Logger LOG = Logger.getLogger("dimtoggle");
    private final Path configDir;
    private final Map<UUID, Long> lastDenial = new HashMap<UUID, Long>();
    private ModConfig config;
    private DimensionLocks locks;
    private int ticks;
    private final Set<String> announcedWarnings = new HashSet<String>();

    public ForgeDimensionControl(ModConfig config, Path configDir) {
        this.config = config;
        this.configDir = configDir;
    }

    @SubscribeEvent
    public void start(ServerStartingEvent event) {
        Path path = event.getServer().getWorldPath(LevelResource.ROOT).resolve("data/dimtoggle-locks.json");
        try {
            locks = DimensionLocks.loadOrInitialize(path, config.restrictedDimensions);
        } catch (IOException exception) {
            throw new IllegalStateException("Cannot load DimToggle lock state", exception);
        }
    }

    @SubscribeEvent
    public void stop(ServerStoppedEvent event) {
        locks = null;
        lastDenial.clear();
    }

    @SubscribeEvent
    public void logout(PlayerEvent.PlayerLoggedOutEvent event) {
        lastDenial.remove(event.getEntity().getUUID());
    }

    @SubscribeEvent
    public void login(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer) {
            checkPlayerLocation((ServerPlayer) event.getEntity());
        }
    }

    @SubscribeEvent
    public void respawn(PlayerEvent.PlayerRespawnEvent event) {
        if (event.getEntity() instanceof ServerPlayer) {
            checkPlayerLocation((ServerPlayer) event.getEntity());
        }
    }

    public boolean isPlayerAllowed(ServerPlayer player, String dimension, long now) {
        dimension = DimensionLocks.normalize(dimension);
        if (locks != null && !locks.isLocked(dimension, now)) return true;
        List<String> groups = new ArrayList<String>();
        if (player.getTeam() != null) {
            groups.add(player.getTeam().getName());
        }
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
    }

    private boolean checkPlayerCapacity(ServerPlayer player, String dimension) {
        ServerLevel target = player.getServer().getLevel(ResourceKey.create(
            net.minecraft.core.Registry.DIMENSION_REGISTRY,
            new ResourceLocation(dimension)
        ));
        int count = target != null ? target.players().size() : 0;
        return AccessPolicy.checkCapacity(config, dimension, count, player.hasPermissions(2));
    }

    private boolean checkPlayerMinLevel(ServerPlayer player, String dimension) {
        return AccessPolicy.checkMinLevel(config, dimension, player.experienceLevel, player.hasPermissions(2));
    }

    private boolean checkPlayerRequiredItem(ServerPlayer player, String dimension) {
        if (player.hasPermissions(2) && config.allowOps) return true;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return true;
        for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
            net.minecraft.world.item.ItemStack stack = player.getInventory().getItem(i);
            if (!stack.isEmpty()) {
                String desc = stack.getItem().getDescriptionId();
                if (desc != null && (desc.contains(req) || stack.getItem().toString().equalsIgnoreCase(req))) return true;
            }
        }
        return false;
    }

    @SubscribeEvent
    public void travel(EntityTravelToDimensionEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer)) return;
        ServerPlayer player = (ServerPlayer) event.getEntity();
        String dimension = DimensionLocks.normalize(event.getDimension().location().toString());
        if (locks == null) {
            event.setCanceled(true);
            return;
        }

        long now = System.currentTimeMillis();

        if (locks.isLocked(dimension, now) && !isPlayerAllowed(player, dimension, now)) {
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou are not allowed to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }

        if (!checkPlayerCapacity(player, dimension)) {
            event.setCanceled(true);
            deny(player, dimension, now, "§cDimension " + dimension + " is full! (" + config.getLimit(dimension) + " players max)");
            bounceFromPortal(player);
            return;
        }

        if (!checkPlayerMinLevel(player, dimension)) {
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou need at least Level " + config.getMinLevel(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }

        if (!checkPlayerRequiredItem(player, dimension)) {
            event.setCanceled(true);
            deny(player, dimension, now, "§cYou must possess a " + config.getRequiredItem(dimension) + " to enter " + dimension + "!");
            bounceFromPortal(player);
            return;
        }

        consumeRequiredItem(player, dimension);
    }

    private void consumeRequiredItem(ServerPlayer player, String dimension) {
        if (!config.isConsumeItem(dimension)) return;
        String req = config.getRequiredItem(dimension);
        if (req == null || req.isEmpty()) return;
        if (player.hasPermissions(2) && config.allowOps) return;
        for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
            net.minecraft.world.item.ItemStack stack = player.getInventory().getItem(i);
            if (!stack.isEmpty()) {
                String desc = stack.getItem().getDescriptionId();
                if (desc != null && (desc.contains(req) || stack.getItem().toString().equalsIgnoreCase(req))) {
                    stack.shrink(1);
                    player.sendMessage(new TextComponent("§e[DimToggle] Consumed 1x " + req + " for entry into " + dimension + "."), Util.NIL_UUID);
                    break;
                }
            }
        }
    }

    private void deny(ServerPlayer player, String dimension, long now, String message) {
        Long last = lastDenial.get(player.getUUID());
        if (last == null || now < last || now - last >= 3000) {
            lastDenial.put(player.getUUID(), now);
            String custom = config.getMessage(dimension);
            String display = custom != null ? "§c[DimToggle] " + custom : message;
            player.sendMessage(new TextComponent(display), Util.NIL_UUID);
        }
    }

    private void bounceFromPortal(ServerPlayer player) {
        player.getServer().execute(() -> {
            if (!player.isAlive()) return;
            double pushX = 0;
            double pushY = 0.35;
            double pushZ = 0;

            BlockPos pos = player.blockPosition();
            BlockState state = player.getLevel().getBlockState(pos);
            if (!state.is(Blocks.NETHER_PORTAL) && !state.is(Blocks.END_PORTAL)) {
                state = player.getLevel().getBlockState(pos.below());
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

            player.teleportTo(player.getLevel(), targetX, targetY, targetZ, player.getYRot(), -10.0f);
            player.setDeltaMovement(pushX * 0.32, 0.35, pushZ * 0.32);
            player.hurtMarked = true;
            player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 45, 3, false, false, true));
            player.playNotifySound(SoundEvents.SHIELD_BLOCK, SoundSource.PLAYERS, 1.0f, 0.6f);
            player.playNotifySound(SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 0.8f, 0.5f);
            try {
                player.getLevel().sendParticles(net.minecraft.core.particles.ParticleTypes.PORTAL, player.getX(), player.getY() + 1.0, player.getZ(), 30, 0.5, 0.5, 0.5, 0.1);
                player.getLevel().sendParticles(net.minecraft.core.particles.ParticleTypes.ENCHANTED_HIT, player.getX(), player.getY() + 1.0, player.getZ(), 20, 0.3, 0.3, 0.3, 0.2);
            } catch (Exception ignored) { }
        });
    }

    private void safeTeleportToSpawn(ServerPlayer player) {
        player.getServer().execute(() -> {
            if (!player.isAlive()) return;
            ServerLevel spawnLevel = player.getServer().getLevel(Level.OVERWORLD);
            if (spawnLevel != null) {
                if (player.getLevel() != spawnLevel && (locks == null || locks.isLocked("minecraft:overworld", System.currentTimeMillis()))) return;
                BlockPos spawnPos = SafeSpawn.find(spawnLevel);
                if (spawnPos == null) return;
                player.teleportTo(spawnLevel, spawnPos.getX() + 0.5, spawnPos.getY(), spawnPos.getZ() + 0.5, player.getYRot(), player.getXRot());
            }
        });
    }

    private void checkPlayerLocation(ServerPlayer player) {
        if (locks == null || player == null || !player.isAlive()) return;
        long now = System.currentTimeMillis();
        String currentDim = DimensionLocks.normalize(player.getLevel().dimension().location().toString());
        if (locks.isLocked(currentDim, now) && !isPlayerAllowed(player, currentDim, now)) {
            safeTeleportToSpawn(player);
            deny(player, currentDim, now, "§cYou are not allowed in " + currentDim + "!");
        }
    }

    private void ejectUnauthorizedPlayers(MinecraftServer server, String dimension) {
        if (server == null || locks == null) return;
        long now = System.currentTimeMillis();
        dimension = DimensionLocks.normalize(dimension);
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            String currentDim = DimensionLocks.normalize(player.getLevel().dimension().location().toString());
            if (currentDim.equals(dimension) && !isPlayerAllowed(player, dimension, now)) {
                safeTeleportToSpawn(player);
                player.sendMessage(new TextComponent("§cYou have been returned to spawn: " + dimension + " is locked!"), Util.NIL_UUID);
            }
        }
    }

    @SubscribeEvent
    public void tick(TickEvent.ServerTickEvent event) {
        if (event.phase != TickEvent.Phase.END || locks == null || ++ticks % 20 != 0) return;
        MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
        if (server == null) return;
        long now = System.currentTimeMillis();
        try {
            for (String dimension : locks.expire(now)) {
                server.getPlayerList().broadcastMessage(new TextComponent("§aDimension unlocked: §f" + dimension), ChatType.SYSTEM, Util.NIL_UUID);
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
                        server.getPlayerList().broadcastMessage(new TextComponent("§6[DimToggle] §fDimension §e" + entry.getKey() + " §fwill unlock in §b" + timeStr + "§f!"), ChatType.SYSTEM, Util.NIL_UUID);
                    }
                }
            }
        }
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            checkPlayerLocation(player);
        }
    }

    @SubscribeEvent
    public void commands(RegisterCommandsEvent event) {
        LiteralCommandNode<CommandSourceStack> dimtoggleNode = event.getDispatcher().register(
            Commands.literal("dimtoggle").requires(source -> source.hasPermission(2))
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
                .then(Commands.literal("reload").executes(context -> reloadConfig(context.getSource())))
        );

        event.getDispatcher().register(Commands.literal("dt").requires(source -> source.hasPermission(2)).redirect(dimtoggleNode));
    }


    private int list(CommandSourceStack source) {
        String text = locks.describe(System.currentTimeMillis());
        StringBuilder extra = new StringBuilder();
        extra.append("\n§eOperators bypass locks: §f").append(config.allowOps);
        extra.append("\n§eSpectators bypass locks: §f").append(config.allowSpectators);
        if (!config.dimensionLimits.isEmpty()) {
            extra.append("\n§6Player Capacity Limits:§f");
            for (Map.Entry<String, Integer> e : config.dimensionLimits.entrySet()) {
                extra.append("\n - ").append(e.getKey()).append(": ").append(e.getValue()).append(" max");
            }
        }
        if (!config.dimensionMinLevel.isEmpty()) {
            extra.append("\n§bXP Level Requirements:§f");
            for (Map.Entry<String, Integer> e : config.dimensionMinLevel.entrySet()) {
                extra.append("\n - ").append(e.getKey()).append(": Level ").append(e.getValue());
            }
        }
        if (!config.dimensionRequiredItem.isEmpty()) {
            extra.append("\n§dRequired Items:§f");
            for (Map.Entry<String, String> e : config.dimensionRequiredItem.entrySet()) {
                extra.append("\n - ").append(e.getKey()).append(": ").append(e.getValue());
            }
        }
        source.sendSuccess(new TextComponent("§e" + text + extra.toString()), false);
        return 1;
    }

    private int getAllowOps(CommandSourceStack source) {
        source.sendSuccess(new TextComponent("§eOperators bypass locks: §f" + config.allowOps), false);
        return 1;
    }

    private int setAllowOps(CommandSourceStack source, boolean enabled) {
        try {
            config.setAllowOps(enabled);
            source.sendSuccess(new TextComponent("§aOperators bypass locks set to: §f" + enabled), true);
            return 1;
        } catch (IOException e) {
            source.sendFailure(new TextComponent("§cFailed to save configuration: " + e.getMessage()));
            return 0;
        }
    }

    private int setLimit(CommandSourceStack source, String rawDimension, int maxPlayers) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            config.setLimit(dimension, maxPlayers);
            source.sendSuccess(new TextComponent("§aSet capacity limit for §f" + dimension + " §ato §f" + maxPlayers + " §aplayers."), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to set limit: " + e.getMessage()));
            return 0;
        }
    }

    private int removeLimit(CommandSourceStack source, String rawDimension) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            config.setLimit(dimension, 0);
            source.sendSuccess(new TextComponent("§aRemoved capacity limit for §f" + dimension), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to remove limit: " + e.getMessage()));
            return 0;
        }
    }

    private int setMinLevel(CommandSourceStack source, String rawDimension, int level) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            config.setMinLevel(dimension, level);
            source.sendSuccess(new TextComponent("§aRequired experience level for §f" + dimension + " §aset to §f" + level), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to set minimum level: " + e.getMessage()));
            return 0;
        }
    }

    private int setRequiredItem(CommandSourceStack source, String rawDimension, String itemId) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            config.setRequiredItem(dimension, itemId);
            source.sendSuccess(new TextComponent("§aRequired item for §f" + dimension + " §aset to §f" + itemId), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to set required item: " + e.getMessage()));
            return 0;
        }
    }

    private int clearRequiredItem(CommandSourceStack source, String rawDimension) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            config.setRequiredItem(dimension, null);
            source.sendSuccess(new TextComponent("§aCleared required item for §f" + dimension), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to clear required item: " + e.getMessage()));
            return 0;
        }
    }

    private int unlock(CommandSourceStack source, String rawDimension) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            if (!locks.unlock(dimension)) {
                source.sendFailure(new TextComponent("§cDimension is not locked: " + dimension));
                return 0;
            }
            source.getServer().getPlayerList().broadcastMessage(new TextComponent("§aDimension unlocked: §f" + dimension), ChatType.SYSTEM, Util.NIL_UUID);
            return 1;
        } catch (IOException exception) {
            source.sendFailure(new TextComponent("§cCould not persist lock update: " + exception.getMessage()));
            return 0;
        }
    }

    private int lock(CommandSourceStack source, String rawDimension, String duration) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            long expiry = duration == null ? 0 : LockDuration.deadline(duration, System.currentTimeMillis());
            locks.lock(dimension, expiry);
            String message = "§aLocked §f" + dimension + (duration == null ? " §apermanently" : " §afor §f" + duration);
            source.sendSuccess(new TextComponent(message), true);
            ejectUnauthorizedPlayers(source.getServer(), dimension);
            return 1;
        } catch (IOException | IllegalArgumentException exception) {
            source.sendFailure(new TextComponent("§cCould not lock dimension: " + exception.getMessage()));
            return 0;
        }
    }

    private int allowUser(CommandSourceStack source, String rawDimension, String player) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            if (config.allowUser(dimension, player)) {
                source.sendSuccess(new TextComponent("§aAllowed player §f" + player + " §ato enter §f" + dimension), true);
                return 1;
            } else {
                source.sendFailure(new TextComponent("§cPlayer §f" + player + " §cis already allowed for §f" + dimension));
                return 0;
            }
        } catch (IOException exception) {
            source.sendFailure(new TextComponent("§cCould not save configuration: " + exception.getMessage()));
            return 0;
        }
    }

    private int disallowUser(CommandSourceStack source, String rawDimension, String player) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            if (config.disallowUser(dimension, player)) {
                source.sendSuccess(new TextComponent("§aRemoved player §f" + player + " §afrom §f" + dimension + " §aallowlist"), true);
                return 1;
            } else {
                source.sendFailure(new TextComponent("§cPlayer §f" + player + " §cis not in §f" + dimension + " §aallowlist"));
                return 0;
            }
        } catch (IOException exception) {
            source.sendFailure(new TextComponent("§cCould not save configuration: " + exception.getMessage()));
            return 0;
        }
    }

    private int allowGroup(CommandSourceStack source, String rawDimension, String group) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            if (config.allowGroup(dimension, group)) {
                source.sendSuccess(new TextComponent("§aAllowed group §f" + group + " §ato enter §f" + dimension), true);
                return 1;
            } else {
                source.sendFailure(new TextComponent("§cGroup §f" + group + " §cis already allowed for §f" + dimension));
                return 0;
            }
        } catch (IOException exception) {
            source.sendFailure(new TextComponent("§cCould not save configuration: " + exception.getMessage()));
            return 0;
        }
    }

    private int disallowGroup(CommandSourceStack source, String rawDimension, String group) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            if (config.disallowGroup(dimension, group)) {
                source.sendSuccess(new TextComponent("§aRemoved group §f" + group + " §afrom §f" + dimension + " §aallowlist"), true);
                return 1;
            } else {
                source.sendFailure(new TextComponent("§cGroup §f" + group + " §cis not in §f" + dimension + " §aallowlist"));
                return 0;
            }
        } catch (IOException exception) {
            source.sendFailure(new TextComponent("§cCould not save configuration: " + exception.getMessage()));
            return 0;
        }
    }

    private int info(CommandSourceStack source, String rawDimension) {
        String dimension = rawDimension == null ? "minecraft:overworld" : DimensionLocks.normalize(rawDimension);
        long now = System.currentTimeMillis();
        boolean locked = locks != null && locks.isLocked(dimension, now);
        Long expiry = locks != null ? locks.snapshot().get(dimension) : null;

        MinecraftServer server = source.getServer();
        int onlineInDim = 0;
        if (server != null) {
            for (ServerPlayer p : server.getPlayerList().getPlayers()) {
                String pDim = DimensionLocks.normalize(p.getLevel().dimension().location().toString());
                if (pDim.equals(dimension)) onlineInDim++;
            }
        }

        StringBuilder sb = new StringBuilder();
        sb.append("§6=== [ DimToggle: §f").append(dimension).append(" §6] ===");
        sb.append("\n§eLock Status: ");
        if (!locked) {
            sb.append("§aUNLOCKED");
        } else if (expiry != null && expiry == 0) {
            sb.append("§cPERMANENTLY LOCKED");
        } else if (expiry != null) {
            long rem = Math.max(0, (expiry - now) / 1000L);
            sb.append("§cLOCKED §7(Expires in ").append(rem / 60L).append("m ").append(rem % 60L).append("s)");
        }

        Integer limit = config.getLimit(dimension);
        sb.append("\n§eCapacity: §f").append(onlineInDim).append(" / ").append(limit != null && limit > 0 ? limit + " max" : "Unlimited");

        int minLvl = config.getMinLevel(dimension);
        sb.append("\n§eMin Level: §f").append(minLvl > 0 ? "Level " + minLvl : "None");

        String reqItem = config.getRequiredItem(dimension);
        boolean consume = config.isConsumeItem(dimension);
        sb.append("\n§eRequired Item: §f").append(reqItem != null ? reqItem + (consume ? " §c(Consumed on entry)" : " §a(Kept)") : "None");

        String customMsg = config.getMessage(dimension);
        if (customMsg != null) {
            sb.append("\n§eLock Notice: §f").append(customMsg);
        }

        List<String> users = config.allowedUsers.get(dimension);
        List<String> groups = config.allowedGroups.get(dimension);
        sb.append("\n§eWhitelisted: §f").append(users != null ? users.size() : 0).append(" players, ").append(groups != null ? groups.size() : 0).append(" groups");

        Map<String, Long> passes = config.getActivePasses(dimension, now);
        sb.append("\n§eActive Passes: §f").append(passes.size());
        for (Map.Entry<String, Long> entry : passes.entrySet()) {
            long rem = Math.max(0, (entry.getValue() - now) / 1000L);
            sb.append("\n - §a").append(entry.getKey()).append(" §7(").append(rem / 60L).append("m remaining)");
        }

        String infoText = sb.toString();
        source.sendSuccess(new TextComponent(infoText), false);
        return 1;
    }

    private int setMessage(CommandSourceStack source, String rawDimension, String message) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            config.setMessage(dimension, message);
            source.sendSuccess(new TextComponent("§aSet lockout notice for §f" + dimension + " §ato: §r" + message), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to set notice: " + e.getMessage()));
            return 0;
        }
    }

    private int clearMessage(CommandSourceStack source, String rawDimension) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            config.setMessage(dimension, null);
            source.sendSuccess(new TextComponent("§aCleared custom lockout notice for §f" + dimension), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to clear notice: " + e.getMessage()));
            return 0;
        }
    }

    private int addPass(CommandSourceStack source, String rawDimension, String player, String duration) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            long expiry = LockDuration.deadline(duration, System.currentTimeMillis());
            config.addPass(dimension, player, expiry);
            source.sendSuccess(new TextComponent("§aGranted §f" + duration + " §aaccess pass for §f" + player + " §ato enter §f" + dimension), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to grant pass: " + e.getMessage()));
            return 0;
        }
    }

    private int revokePass(CommandSourceStack source, String rawDimension, String player) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            if (config.revokePass(dimension, player)) {
                source.sendSuccess(new TextComponent("§aRevoked access pass for §f" + player + " §afrom §f" + dimension), true);
                return 1;
            } else {
                source.sendFailure(new TextComponent("§cPlayer §f" + player + " §cdoes not have an active pass for §f" + dimension));
                return 0;
            }
        } catch (IOException e) {
            source.sendFailure(new TextComponent("§cFailed to revoke pass: " + e.getMessage()));
            return 0;
        }
    }

    private int getAllowSpectators(CommandSourceStack source) {
        source.sendSuccess(new TextComponent("§eSpectators bypass locks: §f" + config.allowSpectators), false);
        return 1;
    }

    private int setAllowSpectators(CommandSourceStack source, boolean enabled) {
        try {
            config.setAllowSpectators(enabled);
            source.sendSuccess(new TextComponent("§aSpectators bypass locks set to: §f" + enabled), true);
            return 1;
        } catch (IOException e) {
            source.sendFailure(new TextComponent("§cFailed to save configuration: " + e.getMessage()));
            return 0;
        }
    }

    private int setConsumeItem(CommandSourceStack source, String rawDimension, boolean enabled) {
        String dimension = DimensionLocks.normalize(rawDimension);
        try {
            config.setConsumeItem(dimension, enabled);
            source.sendSuccess(new TextComponent("§aItem consumption for §f" + dimension + " §aset to: §f" + enabled), true);
            return 1;
        } catch (IOException | IllegalArgumentException e) {
            source.sendFailure(new TextComponent("§cFailed to set item consumption: " + e.getMessage()));
            return 0;
        }
    }

    private int evict(CommandSourceStack source, String rawDimension, boolean evictAll) {
        String dimension = DimensionLocks.normalize(rawDimension);
        MinecraftServer server = source.getServer();
        long now = System.currentTimeMillis();
        int count = 0;
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            String currentDim = DimensionLocks.normalize(player.getLevel().dimension().location().toString());
            if (currentDim.equals(dimension)) {
                if (evictAll || !isPlayerAllowed(player, dimension, now)) {
                    safeTeleportToSpawn(player);
                    player.sendMessage(new TextComponent("§c[DimToggle] You have been evicted from " + dimension + " to spawn."), Util.NIL_UUID);
                    count++;
                }
            }
        }
        final int evictedCount = count;
        source.sendSuccess(new TextComponent("§aEvicted §f" + evictedCount + " §aplayer(s) from §f" + dimension), true);
        return count;
    }

    private int checkPlayer(CommandSourceStack source, String rawDimension, String playerName) {
        String dimension = DimensionLocks.normalize(rawDimension);
        MinecraftServer server = source.getServer();
        ServerPlayer targetPlayer = null;
        for (ServerPlayer p : server.getPlayerList().getPlayers()) {
            if (p.getGameProfile().getName().equalsIgnoreCase(playerName)) {
                targetPlayer = p;
                break;
            }
        }
        if (targetPlayer == null) {
            source.sendFailure(new TextComponent("§cPlayer not found online: " + playerName));
            return 0;
        }
        long now = System.currentTimeMillis();
        boolean locked = locks != null && locks.isLocked(dimension, now);
        boolean allowed = isPlayerAllowed(targetPlayer, dimension, now);
        boolean capOk = checkPlayerCapacity(targetPlayer, dimension);
        boolean lvlOk = checkPlayerMinLevel(targetPlayer, dimension);
        boolean itemOk = checkPlayerRequiredItem(targetPlayer, dimension);
        boolean pass = config.hasPass(dimension, targetPlayer.getStringUUID(), targetPlayer.getGameProfile().getName(), now);

        StringBuilder sb = new StringBuilder();
        sb.append("§6=== [ DimToggle Access Check: §f").append(playerName).append(" -> ").append(dimension).append(" §6] ===");
        sb.append("\n§eDimension Locked: §f").append(locked ? "§cYES" : "§aNO");
        sb.append("\n§eAccess Allowed: §f").append(allowed ? "§aYES" : "§cNO");
        sb.append("\n§eTemporary Pass: §f").append(pass ? "§aACTIVE" : "§7None");
        sb.append("\n§eCapacity Check: §f").append(capOk ? "§aPASS" : "§cFULL");
        sb.append("\n§eLevel Check: §f").append(lvlOk ? "§aPASS" : "§cFAIL (Lvl " + targetPlayer.experienceLevel + " < " + config.getMinLevel(dimension) + ")");
        String req = config.getRequiredItem(dimension);
        if (req != null) {
            sb.append("\n§eRequired Item Check: §f").append(itemOk ? "§aPASS" : "§cMISSING (" + req + ")");
        }
        boolean overall = (!locked || allowed) && capOk && lvlOk && itemOk;
        sb.append("\n§6Final Verdict: §f").append(overall ? "§a§lALLOWED" : "§c§lDENIED ACCESS");

        String infoText = sb.toString();
        source.sendSuccess(new TextComponent(infoText), false);
        return 1;
    }

    private int broadcastToDim(CommandSourceStack source, String rawDimension, String message) {
        String dimension = DimensionLocks.normalize(rawDimension);
        MinecraftServer server = source.getServer();
        int count = 0;
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            String currentDim = DimensionLocks.normalize(player.getLevel().dimension().location().toString());
            if (currentDim.equals(dimension)) {
                player.sendMessage(new TextComponent("§6[" + dimension + "] §f" + message), Util.NIL_UUID);
                count++;
            }
        }
        final int broadcastCount = count;
        source.sendSuccess(new TextComponent("§aBroadcast sent to §f" + broadcastCount + " §aplayer(s) in §f" + dimension), false);
        return count;
    }

    private int reloadConfig(CommandSourceStack source) {
        try {
            this.config = ModConfig.load(configDir);
            source.sendSuccess(new TextComponent("§aDimToggle configuration reloaded."), true);
            return 1;
        } catch (IOException | RuntimeException exception) {
            source.sendFailure(new TextComponent("§cFailed to reload configuration: " + exception.getMessage()));
            return 0;
        }
    }

}
