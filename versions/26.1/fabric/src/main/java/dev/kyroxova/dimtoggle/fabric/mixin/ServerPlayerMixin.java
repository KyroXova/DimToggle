package dev.kyroxova.dimtoggle.fabric.mixin;

import dev.kyroxova.dimtoggle.fabric.FabricDimensionControl;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.portal.TeleportTransition;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ServerPlayer.class)
public abstract class ServerPlayerMixin {
    @Inject(method = "teleport(Lnet/minecraft/world/level/portal/TeleportTransition;)Lnet/minecraft/server/level/ServerPlayer;", at = @At("HEAD"), cancellable = true)
    private void dimtoggle$beforeTravel(TeleportTransition transition, CallbackInfoReturnable<ServerPlayer> callback) {
        if (transition != null && !FabricDimensionControl.mayTravel((ServerPlayer) (Object) this, transition.newLevel().dimension().location().toString()))
            callback.setReturnValue(null);
    }
}
