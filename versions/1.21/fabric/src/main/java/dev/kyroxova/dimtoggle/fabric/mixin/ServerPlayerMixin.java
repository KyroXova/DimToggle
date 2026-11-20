package dev.kyroxova.dimtoggle.fabric.mixin;

import dev.kyroxova.dimtoggle.fabric.FabricDimensionControl;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.portal.DimensionTransition;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ServerPlayer.class)
public abstract class ServerPlayerMixin {
    @Inject(method = "changeDimension", at = @At("HEAD"), cancellable = true)
    private void dimtoggle$beforeTravel(DimensionTransition transition, CallbackInfoReturnable<Entity> callback) {
        if (transition != null && !FabricDimensionControl.mayTravel((ServerPlayer) (Object) this, transition.newLevel().dimension().location().toString()))
            callback.setReturnValue(null);
    }

    @Inject(method = "teleportTo(Lnet/minecraft/server/level/ServerLevel;DDDFF)V", at = @At("HEAD"), cancellable = true)
    private void dimtoggle$beforeTeleport(ServerLevel destination, double x, double y, double z, float yaw, float pitch, CallbackInfo callback) {
        ServerPlayer player = (ServerPlayer) (Object) this;
        if (player.serverLevel() != destination && !FabricDimensionControl.mayTravel(player, destination.dimension().location().toString()))
            callback.cancel();
    }
}
