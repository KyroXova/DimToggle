package dev.kyroxova.dimtoggle.neoforge;

import dev.kyroxova.dimtoggle.TemplateMod;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import dev.kyroxova.dimtoggle.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;
import java.nio.file.Path;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLPaths;

@Mod(TemplateMod.MOD_ID)
public final class Entrypoint {
    public Entrypoint() {
        Path configDir = FMLPaths.CONFIGDIR.get();
        LegacyConfigMigration.migrate(configDir);
        ModConfig config = TemplateMod.initialize(new RuntimePlatform("neoforge", configDir));
        NeoForge.EVENT_BUS.register(new NeoForgeDimensionControl(config, configDir));
    }
}
