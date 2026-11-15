package dev.kyroxova.dimtoggle.platform;

import java.nio.file.Path;

public interface Platform {
    String loader();
    Path configDirectory();
}
