package dev.kyroxova.dimtoggle.util;

import dev.kyroxova.dimtoggle.gameplay.AccessPolicy.Permission;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Collection;
import java.util.List;
import java.util.UUID;

public final class LuckPermsAccess {
    private LuckPermsAccess() { }

    public static Permission check(UUID playerUuid, String node, boolean enabled) {
        if (!enabled || playerUuid == null) return Permission.UNAVAILABLE;
        try {
            Class<?> providerClass = Class.forName("net.luckperms.api.LuckPermsProvider");
            Object provider = providerClass.getMethod("get").invoke(null);
            Class<?> api = Class.forName("net.luckperms.api.LuckPerms");
            Object manager = api.getMethod("getUserManager").invoke(provider);
            Class<?> managerClass = Class.forName("net.luckperms.api.model.user.UserManager");
            Object user = managerClass.getMethod("getUser", UUID.class).invoke(manager, playerUuid);
            if (user == null) return Permission.UNAVAILABLE;
            Class<?> userClass = Class.forName("net.luckperms.api.model.user.User");
            Object cached = userClass.getMethod("getCachedData").invoke(user);
            Class<?> cachedClass = Class.forName("net.luckperms.api.cacheddata.CachedDataManager");
            Object permissions = cachedClass.getMethod("getPermissionData").invoke(cached);
            Class<?> dataClass = Class.forName("net.luckperms.api.cacheddata.CachedPermissionData");
            Class<?> tristateClass = Class.forName("net.luckperms.api.util.Tristate");
            Method asBoolean = tristateClass.getMethod("asBoolean");

            Object result = dataClass.getMethod("checkPermission", String.class).invoke(permissions, node);
            if (Boolean.TRUE.equals(asBoolean.invoke(result))) return Permission.GRANTED;

            Object bypass = dataClass.getMethod("checkPermission", String.class).invoke(permissions, "dimtoggle.bypass");
            if (Boolean.TRUE.equals(asBoolean.invoke(bypass))) return Permission.GRANTED;

            return Permission.DENIED;
        } catch (ReflectiveOperationException | LinkageError exception) {
            return Permission.UNAVAILABLE;
        }
    }

    public static List<String> getGroups(UUID playerUuid) {
        if (playerUuid == null) return Collections.emptyList();
        try {
            Class<?> providerClass = Class.forName("net.luckperms.api.LuckPermsProvider");
            Object provider = providerClass.getMethod("get").invoke(null);
            Class<?> api = Class.forName("net.luckperms.api.LuckPerms");
            Object manager = api.getMethod("getUserManager").invoke(provider);
            Class<?> managerClass = Class.forName("net.luckperms.api.model.user.UserManager");
            Object user = managerClass.getMethod("getUser", UUID.class).invoke(manager, playerUuid);
            if (user == null) return Collections.emptyList();
            Class<?> userClass = Class.forName("net.luckperms.api.model.user.User");
            Object primaryGroup = userClass.getMethod("getPrimaryGroup").invoke(user);
            List<String> groups = new ArrayList<String>();
            if (primaryGroup instanceof String) groups.add((String) primaryGroup);
            Class<?> holderClass = Class.forName("net.luckperms.api.model.PermissionHolder");
            Class<?> optionsClass = Class.forName("net.luckperms.api.query.QueryOptions");
            Object options = holderClass.getMethod("getQueryOptions").invoke(user);
            Object inherited = holderClass.getMethod("getInheritedGroups", optionsClass).invoke(user, options);
            Class<?> groupClass = Class.forName("net.luckperms.api.model.group.Group");
            Method getName = groupClass.getMethod("getName");
            for (Object group : (Collection<?>) inherited) {
                Object name = getName.invoke(group);
                if (name instanceof String && !groups.contains(name)) groups.add((String) name);
            }
            return groups;
        } catch (ReflectiveOperationException | LinkageError exception) {
            return Collections.emptyList();
        }
    }
}
