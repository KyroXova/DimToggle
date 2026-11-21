package dev.kyroxova.dimtoggle.forge;

import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.entity.EntityTravelToDimensionEvent;
import net.minecraftforge.event.server.ServerStartingEvent;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("dimtoggle")
@PrefixGameTestTemplate(false)
public final class DimensionControlGameTests {
    private DimensionControlGameTests() { }

    @GameTest(template = "empty")
    public static void deniesCustomDimensionAndAllowsUnlockedDimension(GameTestHelper helper) throws Exception {
        ServerLevel level = helper.getLevel();
        String blocked = "example:moon";
        DimensionLocks state = DimensionLocks.load(level.getServer().getWorldPath(LevelResource.ROOT).resolve("data/dimtoggle-locks.json"));
        state.lock(blocked, 0);
        ModConfig config = new ModConfig();
        config.enableLuckPerms = false;
        config.allowOps = false;
        config.teleportToSpawn = false;
        ForgeDimensionControl control = new ForgeDimensionControl(config, level.getServer().getWorldPath(LevelResource.ROOT));
        control.start(new ServerStartingEvent(level.getServer()));
        FakePlayer player = FakePlayerFactory.getMinecraft(level);
        ResourceKey<Level> custom = ResourceKey.create(Registries.DIMENSION, new ResourceLocation("example", "moon"));
        EntityTravelToDimensionEvent denied = new EntityTravelToDimensionEvent(player, custom);
        control.travel(denied);
        if (!denied.isCanceled()) { helper.fail("Locked custom dimension was not denied"); return; }
        ResourceKey<Level> open = ResourceKey.create(Registries.DIMENSION, new ResourceLocation("example", "open"));
        EntityTravelToDimensionEvent allowed = new EntityTravelToDimensionEvent(player, open);
        control.travel(allowed);
        if (allowed.isCanceled()) { helper.fail("Unlocked custom dimension was denied"); return; }
        helper.succeed();
    }
}
