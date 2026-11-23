package dev.kyroxova.dimtoggle;

import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.platform.Platform;
import java.io.IOException;
import java.util.logging.Logger;

public final class DimToggleMod {
    public static final String MOD_ID = "dimtoggle";
    private static final Logger LOG = Logger.getLogger(MOD_ID);
    private static ModConfig config;

    private DimToggleMod() { }

    public static ModConfig initialize(Platform platform) {
        try {
            config = ModConfig.load(platform.configDirectory());
            LOG.info("DimToggle initialized on " + platform.loader());
            return config;
        } catch (IOException exception) {
            throw new IllegalStateException("Unable to load DimToggle configuration", exception);
        }
    }

    public static ModConfig getConfig() {
        return config;
    }
}
