package dev.kyroxova.dimtoggle;

import dev.kyroxova.dimtoggle.gameplay.AccessPolicy.Permission;
import dev.kyroxova.dimtoggle.util.LuckPermsAccess;
import java.lang.reflect.Proxy;
import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;
import net.luckperms.api.LuckPerms;
import net.luckperms.api.LuckPermsTestHelper;
import net.luckperms.api.cacheddata.CachedDataManager;
import net.luckperms.api.cacheddata.CachedPermissionData;
import net.luckperms.api.model.group.Group;
import net.luckperms.api.model.user.User;
import net.luckperms.api.model.user.UserManager;
import net.luckperms.api.query.QueryOptions;
import net.luckperms.api.util.Tristate;
import org.junit.Test;
import static org.junit.Assert.*;

public class LuckPermsAccessTest {
    private interface Handler { Object call(String name, Object[] args); }

    private static <T> T stub(Class<T> type, Handler handler) {
        return type.cast(Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[] {type},
            (proxy, method, args) -> handler.call(method.getName(), args)));
    }

    @Test public void explicitDimensionDenialIsNotOverriddenByWildcardAndInheritedGroupsAreRead() throws Exception {
        CachedPermissionData permissions = stub(CachedPermissionData.class, (name, args) -> {
            if (!name.equals("checkPermission")) return null;
            if ("dimtoggle.*".equals(args[0])) return Tristate.TRUE;
            if ("dimtoggle.minecraft.the_end".equals(args[0])) return Tristate.FALSE;
            return Tristate.UNDEFINED;
        });
        CachedDataManager data = stub(CachedDataManager.class, (name, args) -> name.equals("getPermissionData") ? permissions : null);
        Group inherited = stub(Group.class, (name, args) -> name.equals("getName") ? "builders" : null);
        QueryOptions options = stub(QueryOptions.class, (name, args) -> null);
        User user = stub(User.class, (name, args) -> {
            if (name.equals("getCachedData")) return data;
            if (name.equals("getPrimaryGroup")) return "default";
            if (name.equals("getQueryOptions")) return options;
            if (name.equals("getInheritedGroups")) return Collections.singletonList(inherited);
            return null;
        });
        UserManager manager = stub(UserManager.class, (name, args) -> name.equals("getUser") ? user : null);
        LuckPerms provider = stub(LuckPerms.class, (name, args) -> name.equals("getUserManager") ? manager : null);
        LuckPermsTestHelper.register(provider);
        try {
            UUID id = UUID.randomUUID();
            assertEquals(Permission.DENIED, LuckPermsAccess.check(id, "dimtoggle.minecraft.the_end", true));
            assertEquals(Arrays.asList("default", "builders"), LuckPermsAccess.getGroups(id));
        } finally { LuckPermsTestHelper.unregister(); }
    }
}
