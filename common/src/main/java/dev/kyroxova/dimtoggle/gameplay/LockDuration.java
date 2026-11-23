package dev.kyroxova.dimtoggle.gameplay;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class LockDuration {
    private static final Pattern PART = Pattern.compile("([0-9]+)([dhms])");
    private LockDuration() { }

    /** Parse durations such as 2d4h30m into an absolute UTC millisecond deadline. */
    public static long deadline(String input, long nowMillis) {
        if (input == null || input.isEmpty() || nowMillis < 0) throw new IllegalArgumentException("Invalid duration");
        Matcher matcher = PART.matcher(input);
        int position = 0;
        long duration = 0;
        try {
            while (matcher.find()) {
                if (matcher.start() != position) throw new IllegalArgumentException("Invalid duration");
                long multiplier;
                switch (matcher.group(2).charAt(0)) {
                    case 'd': multiplier = 86400000L; break;
                    case 'h': multiplier = 3600000L; break;
                    case 'm': multiplier = 60000L; break;
                    default: multiplier = 1000L;
                }
                duration = Math.addExact(duration, Math.multiplyExact(Long.parseLong(matcher.group(1)), multiplier));
                position = matcher.end();
            }
            if (position != input.length() || duration == 0) throw new IllegalArgumentException("Invalid duration");
            return Math.addExact(nowMillis, duration);
        } catch (ArithmeticException exception) {
            throw new IllegalArgumentException("Duration is too long", exception);
        }
    }
}
