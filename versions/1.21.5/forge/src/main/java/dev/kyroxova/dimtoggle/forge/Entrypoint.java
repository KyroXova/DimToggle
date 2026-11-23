package dev.kyroxova.dimtoggle.forge;

import dev.kyroxova.dimtoggle.DimToggleMod;
import dev.kyroxova.dimtoggle.platform.RuntimePlatform;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.loading.FMLPaths;

@Mod(DimToggleMod.MOD_ID)
public final class Entrypoint {
    public Entrypoint() {
        DimToggleMod.initialize(new RuntimePlatform("forge", FMLPaths.CONFIGDIR.get()));
    }
}
