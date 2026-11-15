package dev.kyroxova.dimtoggle.gameplay;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonParseException;
import com.google.gson.reflect.TypeToken;
import java.io.IOException;
import java.io.Reader;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

/** Persistent lock state. Expiry timestamps are UTC milliseconds; zero means permanent. */
public final class DimensionLocks {
    private static final Pattern DIMENSION = Pattern.compile("[a-z0-9_.-]+:[a-z0-9/._-]+");
    private static final Type MAP_TYPE = new TypeToken<Map<String, Long>>() { }.getType();
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private final Path file;
    private Map<String, Long> locks;

    private DimensionLocks(Path file, Map<String, Long> locks) {
        this.file = file;
        this.locks = locks;
    }

    public static String normalize(String dimension) {
        if (dimension == null) return null;
        dimension = dimension.trim();
        if (dimension.equals("end") || dimension.equals("minecraft:end") || dimension.equals("the_end") || dimension.equals("minecraft:the_end")) return "minecraft:the_end";
        if (dimension.equals("nether") || dimension.equals("minecraft:nether") || dimension.equals("the_nether") || dimension.equals("minecraft:the_nether")) return "minecraft:the_nether";
        if (dimension.equals("overworld") || dimension.equals("minecraft:overworld")) return "minecraft:overworld";
        if (!dimension.contains(":") && !dimension.isEmpty()) return "minecraft:" + dimension;
        return dimension;
    }

    public static DimensionLocks load(Path file) throws IOException {
        Map<String, Long> values = new LinkedHashMap<String, Long>();
        if (Files.exists(file)) {
            try (Reader reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
                Map<String, Long> loaded = GSON.fromJson(reader, MAP_TYPE);
                if (loaded == null) throw new IOException("Empty dimension lock state: " + file);
                for (Map.Entry<String, Long> entry : loaded.entrySet()) {
                    String norm = normalize(entry.getKey());
                    if (!validId(norm) || entry.getValue() == null || entry.getValue() < 0)
                        throw new IOException("Invalid dimension lock state: " + file);
                    values.put(norm, entry.getValue());
                }
            } catch (JsonParseException | IllegalStateException exception) {
                throw new IOException("Invalid dimension lock state: " + file, exception);
            }
        }
        return new DimensionLocks(file, values);
    }

    public static DimensionLocks loadOrInitialize(Path file, List<String> initialDimensions) throws IOException {
        if (Files.exists(file)) return load(file);
        Map<String, Long> initial = new LinkedHashMap<String, Long>();
        for (String dimension : initialDimensions) {
            String norm = normalize(dimension);
            if (!validId(norm)) throw new IOException("Invalid initial dimension ID: " + dimension);
            initial.put(norm, 0L);
        }
        DimensionLocks result = new DimensionLocks(file, initial);
        result.save(initial);
        return result;
    }

    public synchronized void lock(String dimension, long expiresAtMillis) throws IOException {
        dimension = normalize(dimension);
        if (!validId(dimension) || expiresAtMillis < 0) throw new IllegalArgumentException("Invalid lock");
        Map<String, Long> updated = new LinkedHashMap<String, Long>(locks);
        updated.put(dimension, expiresAtMillis);
        save(updated);
        locks = updated;
    }

    public synchronized boolean unlock(String dimension) throws IOException {
        dimension = normalize(dimension);
        if (!locks.containsKey(dimension)) return false;
        Map<String, Long> updated = new LinkedHashMap<String, Long>(locks);
        updated.remove(dimension);
        save(updated);
        locks = updated;
        return true;
    }

    public synchronized boolean isLocked(String dimension, long nowMillis) {
        dimension = normalize(dimension);
        Long expiry = locks.get(dimension);
        return expiry != null && (expiry == 0 || expiry > nowMillis);
    }

    /** Persist expiry before returning dimensions to announce; call from the server thread. */
    public synchronized List<String> expire(long nowMillis) throws IOException {
        Map<String, Long> updated = new LinkedHashMap<String, Long>(locks);
        List<String> expired = new ArrayList<String>();
        for (Map.Entry<String, Long> entry : locks.entrySet()) {
            if (entry.getValue() != 0 && entry.getValue() <= nowMillis) {
                expired.add(entry.getKey());
                updated.remove(entry.getKey());
            }
        }
        if (!expired.isEmpty()) {
            save(updated);
            locks = updated;
        }
        return expired;
    }

    public synchronized Map<String, Long> snapshot() {
        return Collections.unmodifiableMap(new LinkedHashMap<String, Long>(locks));
    }

    public synchronized String describe(long nowMillis) {
        StringBuilder text = new StringBuilder("Dimension locks:");
        for (Map.Entry<String, Long> entry : locks.entrySet()) {
            long expiry = entry.getValue();
            if (expiry != 0 && expiry <= nowMillis) continue;
            text.append("\n").append(entry.getKey()).append(": ");
            if (expiry == 0) text.append("permanent");
            else {
                long remaining = expiry - nowMillis;
                text.append(remaining / 1000 + (remaining % 1000 == 0 ? 0 : 1)).append("s remaining");
            }
        }
        return text.toString();
    }

    public static boolean validId(String dimension) {
        if (dimension == null) return false;
        String normalized = normalize(dimension);
        return DIMENSION.matcher(normalized).matches();
    }

    private void save(Map<String, Long> values) throws IOException {
        Path absolute = file.toAbsolutePath();
        Path parent = absolute.getParent();
        Files.createDirectories(parent);
        Path temporary = Files.createTempFile(parent, "dimtoggle-locks-", ".tmp");
        try {
            Files.write(temporary, (GSON.toJson(values, MAP_TYPE) + "\n").getBytes(StandardCharsets.UTF_8));
            try {
                Files.move(temporary, absolute, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            } catch (AtomicMoveNotSupportedException exception) {
                Files.move(temporary, absolute, StandardCopyOption.REPLACE_EXISTING);
            }
        } finally {
            Files.deleteIfExists(temporary);
        }
    }
}
