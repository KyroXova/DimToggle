package dev.kyroxova.dimtoggle;

import dev.kyroxova.dimtoggle.gameplay.DimensionLocks;
import dev.kyroxova.dimtoggle.gameplay.LockDuration;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import static org.junit.Assert.*;

public class DimensionLocksTest {
    @Rule public TemporaryFolder temporary = new TemporaryFolder();

    @Test public void timedAndPermanentLocksSurviveRestart() throws Exception {
        Path file = temporary.newFolder().toPath().resolve("locks.json");
        DimensionLocks state = DimensionLocks.load(file);
        state.lock("example:moon/deep", 2000);
        state.lock("minecraft:the_end", 0);
        state = DimensionLocks.load(file);
        assertTrue(state.isLocked("example:moon/deep", 1999));
        assertFalse(state.isLocked("example:moon/deep", 2000));
        assertTrue(state.isLocked("minecraft:the_end", Long.MAX_VALUE));
        assertTrue(state.describe(1500).contains("example:moon/deep: 1s remaining"));
        assertFalse(state.describe(2000).contains("example:moon/deep"));
        assertEquals(Arrays.asList("example:moon/deep"), state.expire(2000));
        assertTrue(state.expire(2001).isEmpty());
        assertFalse(DimensionLocks.load(file).snapshot().containsKey("example:moon/deep"));
        assertTrue(state.unlock("minecraft:the_end"));
        assertFalse(state.unlock("minecraft:the_end"));
    }

    @Test public void defaultsAreAppliedOnlyOnFirstStart() throws Exception {
        Path file = temporary.newFolder().toPath().resolve("locks.json");
        DimensionLocks state = DimensionLocks.loadOrInitialize(file, Arrays.asList("minecraft:the_end"));
        assertTrue(state.unlock("minecraft:the_end"));
        assertFalse(DimensionLocks.loadOrInitialize(file, Arrays.asList("minecraft:the_end")).isLocked("minecraft:the_end", 1));
    }

    @Test public void malformedStateFailsWithoutOverwritingFile() throws Exception {
        Path file = temporary.newFile().toPath();
        byte[] data = "{\"invalid dimension\":42}".getBytes(StandardCharsets.UTF_8);
        Files.write(file, data);
        try { DimensionLocks.load(file); fail("Invalid ID must fail"); }
        catch (java.io.IOException expected) { assertArrayEquals(data, Files.readAllBytes(file)); }
    }

    @Test public void rejectsInvalidInput() throws Exception {
        DimensionLocks state = DimensionLocks.load(temporary.newFolder().toPath().resolve("locks.json"));
        try { state.lock("example:Uppercase", 0); fail("Invalid ID must fail"); }
        catch (IllegalArgumentException expected) { assertTrue(state.snapshot().isEmpty()); }
        try { state.lock("example:moon", -1); fail("Negative expiry must fail"); }
        catch (IllegalArgumentException expected) { assertTrue(state.snapshot().isEmpty()); }
    }

    @Test public void failedWriteDoesNotChangeLiveState() throws Exception {
        Path directory = temporary.newFolder().toPath();
        DimensionLocks state = DimensionLocks.load(directory.resolve("locks.json"));
        Files.createDirectory(directory.resolve("locks.json"));
        try { state.lock("example:moon", 0); fail("Write must fail"); }
        catch (java.io.IOException expected) { assertTrue(state.snapshot().isEmpty()); }
    }

    @Test public void durationParsingChecksSyntaxAndOverflow() {
        assertEquals(90062000L, LockDuration.deadline("1d1h1m1s", 1000));
        for (String invalid : Arrays.asList("", "0s", "1h!", "2w", "999999999999999999999d")) {
            try { LockDuration.deadline(invalid, 1); fail("Expected invalid duration: " + invalid); }
            catch (IllegalArgumentException expected) { }
        }
        try { LockDuration.deadline("1s", Long.MAX_VALUE); fail("Overflow must fail"); }
        catch (IllegalArgumentException expected) { }
    }
}
