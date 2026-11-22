package dev.kyroxova.dimtoggle;

import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.platform.Platform;

/**
 * Primary API and state access for DimToggle.
 */
public final class DimToggle {
    public static final String MOD_ID = DimToggleMod.MOD_ID;

    private DimToggle() { }

    public static ModConfig initialize(Platform platform) {
        return DimToggleMod.initialize(platform);
    }

    public static ModConfig getConfig() {
        return DimToggleMod.getConfig();
    }
}
