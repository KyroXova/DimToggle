package dev.kyroxova.dimtoggle.fabric;

import dev.kyroxova.dimtoggle.DimToggleMod;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import dev.kyroxova.dimtoggle.config.ModConfig;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import java.nio.file.Path;

public final class Entrypoint implements ModInitializer {
    public void onInitialize() {
        Path configDir = FabricLoader.getInstance().getConfigDir();
        DimToggleMod.initialize(new RuntimePlatform("fabric", configDir));
    }
}
