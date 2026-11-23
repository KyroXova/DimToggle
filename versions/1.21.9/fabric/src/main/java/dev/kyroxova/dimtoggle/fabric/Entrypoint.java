package dev.kyroxova.dimtoggle.fabric;

import dev.kyroxova.dimtoggle.DimToggleMod;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;

public final class Entrypoint implements ModInitializer {
    public void onInitialize() {
        DimToggleMod.initialize(new RuntimePlatform("fabric", FabricLoader.getInstance().getConfigDir()));
    }
}
