package dev.kyroxova.dimtoggle.forge;

import dev.kyroxova.dimtoggle.DimToggleMod;
import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import java.nio.file.Path;
import net.minecraftforge.common.MinecraftForge;
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
