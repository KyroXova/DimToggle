package dev.kyroxova.dimtoggle;

import dev.kyroxova.dimtoggle.config.ModConfig;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy;
import dev.kyroxova.dimtoggle.gameplay.AccessPolicy.Permission;
import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import dev.kyroxova.dimtoggle.util.LuckPermsAccess;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import static org.junit.Assert.*;

public class CoreTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();

    @Test public void permissionNodesPreserveCustomDimensionPaths() {
        assertEquals("dimtoggle.example.dimension/path", AccessPolicy.permissionNode("example:dimension/path"));
    }

    @Test public void accessPolicyEvaluatesComprehensiveRules() throws Exception {
        Path file = temporary.newFolder().toPath().resolve("locks.json");
        DimensionLocks locks = DimensionLocks.load(file);
        locks.lock("minecraft:the_nether", 0);

        ModConfig config = new ModConfig();
        config.allowUser("minecraft:the_nether", "BuilderBob");
        config.allowGroup("minecraft:the_nether", "builders");

        // Unlocked dimension allows all
        assertTrue(AccessPolicy.mayEnter(config, locks, "minecraft:overworld", 1000, "uuid1", "Player1", Collections.emptyList(), Permission.DENIED, false));

        // Allowlisted user allows access
        assertTrue(AccessPolicy.mayEnter(config, locks, "minecraft:the_nether", 1000, "uuid-bob", "BuilderBob", Collections.emptyList(), Permission.UNAVAILABLE, false));

        // Allowlisted group allows access
        assertTrue(AccessPolicy.mayEnter(config, locks, "minecraft:the_nether", 1000, "uuid2", "RandomPlayer", Arrays.asList("builders"), Permission.UNAVAILABLE, false));

        // Operator denied if allowOps is false and not on list
        assertFalse(AccessPolicy.mayEnter(config, locks, "minecraft:the_nether", 1000, "uuid3", "Admin", Collections.emptyList(), Permission.UNAVAILABLE, true));

        // Operator allows access if allowOps is true
        config.allowOps = true;
        assertTrue(AccessPolicy.mayEnter(config, locks, "minecraft:the_nether", 1000, "uuid3", "Admin", Collections.emptyList(), Permission.UNAVAILABLE, true));
        config.allowOps = false;

        // LuckPerms granted allows access
        assertTrue(AccessPolicy.mayEnter(config, locks, "minecraft:the_nether", 1000, "uuid4", "Permitted", Collections.emptyList(), Permission.GRANTED, false));

        // Random unauthorized player denied
        assertFalse(AccessPolicy.mayEnter(config, locks, "minecraft:the_nether", 1000, "uuid5", "Intruder", Collections.emptyList(), Permission.DENIED, false));
    }

    @Test public void userAndGroupAllowlistsPersist() throws Exception {
        Path directory = temporary.newFolder().toPath();
        ModConfig config = ModConfig.load(directory);
        assertTrue(config.allowUser("minecraft:the_end", "Alice"));
        assertFalse(config.allowUser("minecraft:the_end", "Alice")); // duplicate ignored
        assertTrue(config.isUserAllowed("minecraft:the_end", null, "Alice"));
        assertTrue(config.isUserAllowed("minecraft:the_end", null, "alice")); // case insensitive

        assertTrue(config.allowGroup("minecraft:the_end", "VIP"));
        assertTrue(config.isGroupAllowed("minecraft:the_end", Arrays.asList("vip")));

        // Reload from file to ensure persistence
        ModConfig reloaded = ModConfig.load(directory);
        assertTrue(reloaded.isUserAllowed("minecraft:the_end", null, "Alice"));
        assertTrue(reloaded.isGroupAllowed("minecraft:the_end", Arrays.asList("vip")));

        // Disallow removes
        assertTrue(reloaded.disallowUser("minecraft:the_end", "Alice"));
        assertFalse(reloaded.isUserAllowed("minecraft:the_end", null, "Alice"));
        assertTrue(reloaded.disallowGroup("minecraft:the_end", "VIP"));
        assertFalse(reloaded.isGroupAllowed("minecraft:the_end", Arrays.asList("vip")));
    }

    @Test public void luckPermsAccessHandlesNullGracefully() {
        assertEquals(Permission.UNAVAILABLE, LuckPermsAccess.check(null, "dimtoggle.test", true));
        assertEquals(Permission.UNAVAILABLE, LuckPermsAccess.check(UUID.randomUUID(), "dimtoggle.test", false));
        assertTrue(LuckPermsAccess.getGroups(null).isEmpty());
    }

    @Test public void configPersistsAndReadsUserValues() throws Exception {
        Path directory = temporary.newFolder().toPath();
        assertTrue(ModConfig.load(directory).restrictedDimensions.contains("minecraft:the_end"));
        Files.write(directory.resolve("dimtoggle.json"), "{\"restrictedDimensions\":[\"example:world\"]}".getBytes(StandardCharsets.UTF_8));
        assertEquals("example:world", ModConfig.load(directory).restrictedDimensions.get(0));
    }

    @Test public void invalidConfigIsPreserved() throws Exception {
        Path directory = temporary.newFolder().toPath();
        Path config = directory.resolve("dimtoggle.json");
        byte[] content = "{\"restrictedDimensions\":null}".getBytes(StandardCharsets.UTF_8);
        Files.write(config, content);
        try { ModConfig.load(directory); fail("Expected invalid configuration to fail"); }
        catch (IllegalArgumentException expected) { assertArrayEquals(content, Files.readAllBytes(config)); }
    }

    @Test public void failedAllowlistWriteDoesNotGrantAccess() throws Exception {
        Path directory = temporary.newFolder().toPath();
        Files.createDirectory(directory.resolve("dimtoggle.json"));
        ModConfig config = new ModConfig();
        try { config.writeNew(directory); fail("Expected write failure"); }
        catch (java.io.IOException expected) { }
        try { config.allowUser("minecraft:the_end", "Alice"); fail("Expected write failure"); }
        catch (java.io.IOException expected) { assertFalse(config.isUserAllowed("minecraft:the_end", null, "Alice")); }
    }

    @Test public void rejectsInvalidAllowlistWithoutOverwriting() throws Exception {
        Path directory = temporary.newFolder().toPath();
        Path config = directory.resolve("dimtoggle.json");
        byte[] content = "{\"allowedUsers\":{\"minecraft:the_end\":[null]}}".getBytes(StandardCharsets.UTF_8);
        Files.write(config, content);
        try { ModConfig.load(directory); fail("Expected invalid allowlist to fail"); }
        catch (IllegalArgumentException expected) { assertArrayEquals(content, Files.readAllBytes(config)); }
    }

    @Test public void capacityLimitsAndProgressionRequirementsPersist() throws Exception {
        Path directory = temporary.newFolder().toPath();
        ModConfig config = ModConfig.load(directory);
        
        config.setLimit("minecraft:the_nether", 5);
        assertEquals(Integer.valueOf(5), config.getLimit("minecraft:the_nether"));
        
        config.setMinLevel("minecraft:the_nether", 20);
        assertEquals(20, config.getMinLevel("minecraft:the_nether"));
        
        config.setRequiredItem("minecraft:the_end", "minecraft:eye_of_ender");
        assertEquals("minecraft:eye_of_ender", config.getRequiredItem("minecraft:the_end"));

        // Reload
        ModConfig reloaded = ModConfig.load(directory);
        assertEquals(Integer.valueOf(5), reloaded.getLimit("minecraft:the_nether"));
        assertEquals(20, reloaded.getMinLevel("minecraft:the_nether"));
        assertEquals("minecraft:eye_of_ender", reloaded.getRequiredItem("minecraft:the_end"));

        // Capacity evaluations
        assertTrue(AccessPolicy.checkCapacity(reloaded, "minecraft:the_nether", 4, false));
        assertFalse(AccessPolicy.checkCapacity(reloaded, "minecraft:the_nether", 5, false));
        assertFalse(AccessPolicy.checkCapacity(reloaded, "minecraft:the_nether", 6, false));
        
        // Operator bypasses capacity if allowOps is true
        assertFalse(AccessPolicy.checkCapacity(reloaded, "minecraft:the_nether", 5, true));
        reloaded.allowOps = true;
        assertTrue(AccessPolicy.checkCapacity(reloaded, "minecraft:the_nether", 5, true));

        // Progression evaluations
        reloaded.allowOps = false;
        assertTrue(AccessPolicy.checkMinLevel(reloaded, "minecraft:the_nether", 25, false));
        assertTrue(AccessPolicy.checkMinLevel(reloaded, "minecraft:the_nether", 20, false));
        assertFalse(AccessPolicy.checkMinLevel(reloaded, "minecraft:the_nether", 19, false));

        // Removal
        reloaded.setLimit("minecraft:the_nether", 0);
        assertNull(reloaded.getLimit("minecraft:the_nether"));
        reloaded.setMinLevel("minecraft:the_nether", 0);
        assertEquals(0, reloaded.getMinLevel("minecraft:the_nether"));
        reloaded.setRequiredItem("minecraft:the_end", "none");
        assertNull(reloaded.getRequiredItem("minecraft:the_end"));
    }

    @Test public void extendedGovernanceFeaturesPersistAndEvaluate() throws Exception {
        Path directory = temporary.newFolder().toPath();
        ModConfig config = ModConfig.load(directory);

        // Spectator bypass
        assertFalse(config.allowSpectators);
        config.setAllowSpectators(true);
        assertTrue(config.allowSpectators);

        // Custom messages
        config.setMessage("minecraft:the_end", "Dragon fight event in progress!");
        assertEquals("Dragon fight event in progress!", config.getMessage("minecraft:the_end"));

        // Item consumption
        assertFalse(config.isConsumeItem("minecraft:the_nether"));
        config.setConsumeItem("minecraft:the_nether", true);
        assertTrue(config.isConsumeItem("minecraft:the_nether"));

        // Temporary passes
        long now = System.currentTimeMillis();
        config.addPass("minecraft:the_end", "SpecialGuest", now + 3600000L); // 1 hr pass
        assertTrue(config.hasPass("minecraft:the_end", null, "SpecialGuest", now + 1000L));
        assertFalse(config.hasPass("minecraft:the_end", null, "SpecialGuest", now + 4000000L)); // expired

        // Reload to verify persistence
        ModConfig reloaded = ModConfig.load(directory);
        assertTrue(reloaded.allowSpectators);
        assertEquals("Dragon fight event in progress!", reloaded.getMessage("minecraft:the_end"));
        assertTrue(reloaded.isConsumeItem("minecraft:the_nether"));
        assertTrue(reloaded.hasPass("minecraft:the_end", null, "SpecialGuest", now + 1000L));

        // Evaluate AccessPolicy with temporary pass
        Path locksFile = directory.resolve("locks.json");
        DimensionLocks locks = DimensionLocks.load(locksFile);
        locks.lock("minecraft:the_end", 0); // locked permanently
        
        // Pass grants access
        assertTrue(AccessPolicy.mayEnter(reloaded, locks, "minecraft:the_end", now + 1000L, "uuid-guest", "SpecialGuest", Collections.emptyList(), Permission.UNAVAILABLE, false, false));
        // Another player without pass denied
        assertFalse(AccessPolicy.mayEnter(reloaded, locks, "minecraft:the_end", now + 1000L, "uuid-other", "OtherPlayer", Collections.emptyList(), Permission.UNAVAILABLE, false, false));
        // Spectator grants access when allowSpectators is true
        assertTrue(AccessPolicy.mayEnter(reloaded, locks, "minecraft:the_end", now + 1000L, "uuid-spec", "SpectatorPlayer", Collections.emptyList(), Permission.UNAVAILABLE, false, true));

        // Revoke pass
        assertTrue(reloaded.revokePass("minecraft:the_end", "SpecialGuest"));
        assertFalse(reloaded.hasPass("minecraft:the_end", null, "SpecialGuest", now + 1000L));
        assertFalse(AccessPolicy.mayEnter(reloaded, locks, "minecraft:the_end", now + 1000L, "uuid-guest", "SpecialGuest", Collections.emptyList(), Permission.UNAVAILABLE, false, false));
    }
}
