package dev.kyroxova.dimtoggle.neoforge;

import com.electronwill.nightconfig.core.CommentedConfig;
import com.electronwill.nightconfig.toml.TomlParser;
import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

final class LegacyConfigMigration {
    private LegacyConfigMigration() { }

    static void migrate(Path directory) {
        Path oldFile = directory.resolve("dimtoggle-common.toml");
        if (Files.exists(directory.resolve("dimtoggle.json")) || !Files.isRegularFile(oldFile)) return;
        try (Reader reader = Files.newBufferedReader(oldFile, StandardCharsets.UTF_8)) {
            CommentedConfig old = new TomlParser().parse(reader);
            Object luckPerms = old.get("enableLuckPerms");
            Object spawn = old.get("teleportToSpawn");
            Object dimensions = old.get("restrictedDimensions");
            if (!(luckPerms instanceof Boolean) || !(spawn instanceof Boolean) || !(dimensions instanceof List<?>))
                throw new IOException("Missing or invalid legacy settings");
            ModConfig config = new ModConfig();
            config.enableLuckPerms = (Boolean) luckPerms;
            config.teleportToSpawn = (Boolean) spawn;
            config.restrictedDimensions = new ArrayList<String>();
            for (Object dimension : (List<?>) dimensions) {
                if (!(dimension instanceof String) || !DimensionLocks.validId((String) dimension))
                    throw new IOException("Invalid dimension ID in legacy settings");
                config.restrictedDimensions.add((String) dimension);
            }
            config.writeNew(directory);
        } catch (IOException | RuntimeException exception) {
            throw new IllegalStateException("Could not migrate DimToggle configuration from " + oldFile, exception);
        }
    }
}
