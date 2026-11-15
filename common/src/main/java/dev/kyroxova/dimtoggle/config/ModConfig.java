package dev.kyroxova.dimtoggle.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ModConfig {
    public boolean enableLuckPerms = true;
    public boolean teleportToSpawn = true;
    public boolean allowOps = false;
    public boolean allowSpectators = false;
    public List<String> restrictedDimensions = new ArrayList<String>(Arrays.asList("minecraft:the_end", "minecraft:the_nether"));
    public Map<String, List<String>> allowedUsers = new LinkedHashMap<String, List<String>>();
    public Map<String, List<String>> allowedGroups = new LinkedHashMap<String, List<String>>();
    public Map<String, Integer> dimensionLimits = new LinkedHashMap<String, Integer>();
    public Map<String, Integer> dimensionMinLevel = new LinkedHashMap<String, Integer>();
    public Map<String, String> dimensionRequiredItem = new LinkedHashMap<String, String>();
    public Map<String, String> customMessages = new LinkedHashMap<String, String>();
    public Map<String, Boolean> consumeItem = new LinkedHashMap<String, Boolean>();
    public Map<String, Map<String, Long>> temporaryPasses = new LinkedHashMap<String, Map<String, Long>>();

    private transient Path configPath;

    public static ModConfig load(Path directory) throws IOException {
        Files.createDirectories(directory);
        Path file = directory.resolve("dimtoggle.json");
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        if (!Files.exists(file)) {
            ModConfig defaults = new ModConfig();
            defaults.writeNew(directory);
            return defaults;
        }
        try (Reader reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            ModConfig config = gson.fromJson(reader, ModConfig.class);
            if (config == null || config.restrictedDimensions == null || config.restrictedDimensions.contains(null)) {
                throw new IllegalArgumentException("Invalid dimtoggle.json: restrictedDimensions must be a list of dimension IDs");
            }
            if (config.allowedUsers == null || config.allowedGroups == null)
                throw new IllegalArgumentException("Invalid dimtoggle.json: allowlists must be objects");
            if (config.dimensionLimits == null) config.dimensionLimits = new LinkedHashMap<String, Integer>();
            if (config.dimensionMinLevel == null) config.dimensionMinLevel = new LinkedHashMap<String, Integer>();
            if (config.dimensionRequiredItem == null) config.dimensionRequiredItem = new LinkedHashMap<String, String>();
            if (config.customMessages == null) config.customMessages = new LinkedHashMap<String, String>();
            if (config.consumeItem == null) config.consumeItem = new LinkedHashMap<String, Boolean>();
            if (config.temporaryPasses == null) config.temporaryPasses = new LinkedHashMap<String, Map<String, Long>>();
            validateAllowlist(config.allowedUsers);
            validateAllowlist(config.allowedGroups);
            for (String dimension : config.restrictedDimensions) {
                if (!DimensionLocks.validId(dimension)) throw new IllegalArgumentException("Invalid dimension ID: " + dimension);
            }
            config.configPath = file;
            return config;
        }
    }

    public synchronized void save() throws IOException {
        if (configPath == null) return;
        Path parent = configPath.getParent();
        if (parent != null) Files.createDirectories(parent);
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        Path temp = Files.createTempFile(parent != null ? parent : configPath.toAbsolutePath().getParent(), "dimtoggle-config-", ".tmp");
        try {
            Files.write(temp, (gson.toJson(this) + "\n").getBytes(StandardCharsets.UTF_8));
            try {
                Files.move(temp, configPath, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(temp, configPath, StandardCopyOption.REPLACE_EXISTING);
            }
        } finally {
            Files.deleteIfExists(temp);
        }
    }

    public void writeNew(Path directory) throws IOException {
        Files.createDirectories(directory);
        configPath = directory.resolve("dimtoggle.json");
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        Files.write(configPath, (gson.toJson(this) + "\n").getBytes(StandardCharsets.UTF_8), StandardOpenOption.CREATE_NEW);
    }

    private static void validateAllowlist(Map<String, List<String>> entries) {
        for (Map.Entry<String, List<String>> entry : entries.entrySet()) {
            if (!DimensionLocks.validId(entry.getKey()) || entry.getValue() == null || entry.getValue().contains(null))
                throw new IllegalArgumentException("Invalid allowlist for dimension: " + entry.getKey());
        }
    }

    public synchronized void setAllowOps(boolean allow) throws IOException {
        this.allowOps = allow;
        save();
    }

    public synchronized boolean isUserAllowed(String dimension, String uuidStr, String username) {
        dimension = DimensionLocks.normalize(dimension);
        List<String> users = allowedUsers.get(dimension);
        if (users == null || users.isEmpty()) return false;
        for (String user : users) {
            if (uuidStr != null && user.equalsIgnoreCase(uuidStr)) return true;
            if (username != null && user.equalsIgnoreCase(username)) return true;
        }
        return false;
    }

    public synchronized boolean isGroupAllowed(String dimension, List<String> groups) {
        dimension = DimensionLocks.normalize(dimension);
        if (groups == null || groups.isEmpty()) return false;
        List<String> allowed = allowedGroups.get(dimension);
        if (allowed == null || allowed.isEmpty()) return false;
        for (String group : groups) {
            for (String target : allowed) {
                if (target.equalsIgnoreCase(group)) return true;
            }
        }
        return false;
    }

    public synchronized boolean allowUser(String dimension, String user) throws IOException {
        return updateAllowlist(allowedUsers, dimension, user, true);
    }

    public synchronized boolean disallowUser(String dimension, String user) throws IOException {
        return updateAllowlist(allowedUsers, dimension, user, false);
    }

    public synchronized boolean allowGroup(String dimension, String group) throws IOException {
        return updateAllowlist(allowedGroups, dimension, group, true);
    }

    public synchronized boolean disallowGroup(String dimension, String group) throws IOException {
        return updateAllowlist(allowedGroups, dimension, group, false);
    }

    private boolean updateAllowlist(Map<String, List<String>> entries, String dimension, String name, boolean add) throws IOException {
        dimension = DimensionLocks.normalize(dimension);
        if (!DimensionLocks.validId(dimension) || name == null || name.trim().isEmpty())
            throw new IllegalArgumentException("Invalid dimension or allowlist entry");
        List<String> original = entries.get(dimension);
        List<String> updated = original == null ? new ArrayList<String>() : new ArrayList<String>(original);
        boolean found = false;
        for (int i = updated.size() - 1; i >= 0; i--) {
            if (updated.get(i).equalsIgnoreCase(name)) {
                found = true;
                if (!add) updated.remove(i);
            }
        }
        if (add == found) return false;
        if (add) updated.add(name);
        if (updated.isEmpty()) entries.remove(dimension); else entries.put(dimension, updated);
        try {
            save();
        } catch (IOException exception) {
            if (original == null) entries.remove(dimension); else entries.put(dimension, original);
            throw exception;
        }
        return true;
    }

    public synchronized boolean setLimit(String dimension, int maxPlayers) throws IOException {
        dimension = DimensionLocks.normalize(dimension);
        if (!DimensionLocks.validId(dimension) || maxPlayers < 0)
            throw new IllegalArgumentException("Invalid dimension or capacity limit");
        if (maxPlayers == 0) {
            dimensionLimits.remove(dimension);
        } else {
            dimensionLimits.put(dimension, maxPlayers);
        }
        save();
        return true;
    }

    public synchronized Integer getLimit(String dimension) {
        dimension = DimensionLocks.normalize(dimension);
        return dimensionLimits.get(dimension);
    }

    public synchronized boolean setMinLevel(String dimension, int level) throws IOException {
        dimension = DimensionLocks.normalize(dimension);
        if (!DimensionLocks.validId(dimension) || level < 0)
            throw new IllegalArgumentException("Invalid dimension or minimum level");
        if (level == 0) {
            dimensionMinLevel.remove(dimension);
        } else {
            dimensionMinLevel.put(dimension, level);
        }
        save();
        return true;
    }

    public synchronized int getMinLevel(String dimension) {
        dimension = DimensionLocks.normalize(dimension);
        Integer level = dimensionMinLevel.get(dimension);
        return level != null ? level : 0;
    }

    public synchronized boolean setRequiredItem(String dimension, String itemId) throws IOException {
        dimension = DimensionLocks.normalize(dimension);
        if (!DimensionLocks.validId(dimension))
            throw new IllegalArgumentException("Invalid dimension ID");
        if (itemId == null || itemId.trim().isEmpty() || itemId.equalsIgnoreCase("none")) {
            dimensionRequiredItem.remove(dimension);
        } else {
            dimensionRequiredItem.put(dimension, itemId.trim());
        }
        save();
        return true;
    }

    public synchronized String getRequiredItem(String dimension) {
        dimension = DimensionLocks.normalize(dimension);
        return dimensionRequiredItem.get(dimension);
    }

    public synchronized void setAllowSpectators(boolean allow) throws IOException {
        this.allowSpectators = allow;
        save();
    }

    public synchronized boolean setMessage(String dimension, String message) throws IOException {
        dimension = DimensionLocks.normalize(dimension);
        if (!DimensionLocks.validId(dimension)) throw new IllegalArgumentException("Invalid dimension ID: " + dimension);
        if (message == null || message.trim().isEmpty()) {
            customMessages.remove(dimension);
        } else {
            customMessages.put(dimension, message.trim());
        }
        save();
        return true;
    }

    public synchronized String getMessage(String dimension) {
        dimension = DimensionLocks.normalize(dimension);
        return customMessages.get(dimension);
    }

    public synchronized boolean setConsumeItem(String dimension, boolean consume) throws IOException {
        dimension = DimensionLocks.normalize(dimension);
        if (!DimensionLocks.validId(dimension)) throw new IllegalArgumentException("Invalid dimension ID: " + dimension);
        if (!consume) {
            consumeItem.remove(dimension);
        } else {
            consumeItem.put(dimension, Boolean.TRUE);
        }
        save();
        return true;
    }

    public synchronized boolean isConsumeItem(String dimension) {
        dimension = DimensionLocks.normalize(dimension);
        Boolean val = consumeItem.get(dimension);
        return val != null && val.booleanValue();
    }

    public synchronized boolean addPass(String dimension, String player, long expiresAtMillis) throws IOException {
        dimension = DimensionLocks.normalize(dimension);
        if (!DimensionLocks.validId(dimension) || player == null || player.trim().isEmpty() || expiresAtMillis <= 0)
            throw new IllegalArgumentException("Invalid pass parameters");
        Map<String, Long> dimPasses = temporaryPasses.get(dimension);
        if (dimPasses == null) {
            dimPasses = new LinkedHashMap<String, Long>();
            temporaryPasses.put(dimension, dimPasses);
        }
        dimPasses.put(player.trim(), expiresAtMillis);
        save();
        return true;
    }

    public synchronized boolean revokePass(String dimension, String player) throws IOException {
        dimension = DimensionLocks.normalize(dimension);
        if (player == null) return false;
        Map<String, Long> dimPasses = temporaryPasses.get(dimension);
        if (dimPasses == null) return false;
        boolean removed = false;
        for (Map.Entry<String, Long> entry : new ArrayList<Map.Entry<String, Long>>(dimPasses.entrySet())) {
            if (entry.getKey().equalsIgnoreCase(player.trim())) {
                dimPasses.remove(entry.getKey());
                removed = true;
            }
        }
        if (dimPasses.isEmpty()) temporaryPasses.remove(dimension);
        if (removed) save();
        return removed;
    }

    public synchronized boolean hasPass(String dimension, String uuidStr, String username, long nowMillis) {
        dimension = DimensionLocks.normalize(dimension);
        Map<String, Long> dimPasses = temporaryPasses.get(dimension);
        if (dimPasses == null || dimPasses.isEmpty()) return false;
        for (Map.Entry<String, Long> entry : dimPasses.entrySet()) {
            if (entry.getValue() != null && entry.getValue().longValue() > nowMillis) {
                if (uuidStr != null && entry.getKey().equalsIgnoreCase(uuidStr)) return true;
                if (username != null && entry.getKey().equalsIgnoreCase(username)) return true;
            }
        }
        return false;
    }

    public synchronized Map<String, Long> getActivePasses(String dimension, long nowMillis) {
        dimension = DimensionLocks.normalize(dimension);
        Map<String, Long> dimPasses = temporaryPasses.get(dimension);
        Map<String, Long> active = new LinkedHashMap<String, Long>();
        if (dimPasses != null) {
            for (Map.Entry<String, Long> entry : dimPasses.entrySet()) {
                if (entry.getValue() != null && entry.getValue().longValue() > nowMillis) {
                    active.put(entry.getKey(), entry.getValue());
                }
            }
        }
        return active;
    }
}
