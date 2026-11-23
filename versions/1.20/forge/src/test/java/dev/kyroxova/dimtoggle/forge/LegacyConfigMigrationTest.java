package dev.kyroxova.dimtoggle.forge;

import dev.kyroxova.dimtoggle.config.ModConfig;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import static org.junit.Assert.*;

public class LegacyConfigMigrationTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();

    @Test public void migratesOriginalSettingsOnce() throws Exception {
        Path directory = temporary.newFolder().toPath();
        Path legacy = directory.resolve("dimtoggle-common.toml");
        Files.write(legacy, ("enableLuckPerms = false\nteleportToSpawn = true\n" +
            "restrictedDimensions = [\"example:moon\", \"minecraft:the_end\"]\n").getBytes(StandardCharsets.UTF_8));
        LegacyConfigMigration.migrate(directory);
        ModConfig config = ModConfig.load(directory);
        assertFalse(config.enableLuckPerms);
        assertTrue(config.teleportToSpawn);
        assertEquals("example:moon", config.restrictedDimensions.get(0));
        byte[] json = Files.readAllBytes(directory.resolve("dimtoggle.json"));
        Files.write(legacy, "broken".getBytes(StandardCharsets.UTF_8));
        LegacyConfigMigration.migrate(directory);
        assertArrayEquals(json, Files.readAllBytes(directory.resolve("dimtoggle.json")));
    }

    @Test public void refusesMalformedLegacyWithoutCreatingJson() throws Exception {
        Path directory = temporary.newFolder().toPath();
        Files.write(directory.resolve("dimtoggle-common.toml"), "enableLuckPerms = true\n".getBytes(StandardCharsets.UTF_8));
        try { LegacyConfigMigration.migrate(directory); fail("Expected migration failure"); }
        catch (IllegalStateException expected) { assertFalse(Files.exists(directory.resolve("dimtoggle.json"))); }
    }
}
