package dev.kyroxova.dimtoggle.neoforge;

import dev.kyroxova.dimtoggle.DimToggleMod;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLPaths;

@Mod(DimToggleMod.MOD_ID)
public final class Entrypoint {
    public Entrypoint() {
        DimToggleMod.initialize(new RuntimePlatform("neoforge", FMLPaths.CONFIGDIR.get()));
    }
}
