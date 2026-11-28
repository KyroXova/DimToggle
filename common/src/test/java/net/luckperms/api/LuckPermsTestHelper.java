package net.luckperms.api;

/**
 * Test helper in the net.luckperms.api package to access package-private
 * registration methods on LuckPermsProvider without reflection or setAccessible().
 */
public final class LuckPermsTestHelper {
    private LuckPermsTestHelper() {}

    public static void register(LuckPerms provider) {
        LuckPermsProvider.register(provider);
    }

    public static void unregister() {
        LuckPermsProvider.unregister();
    }
}
