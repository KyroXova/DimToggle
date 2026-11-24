package dev.kyroxova.dimtoggle.fabric.mixin;

import dev.kyroxova.dimtoggle.fabric.FabricDimensionControl;
import java.util.function.BooleanSupplier;
import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(MinecraftServer.class)
public abstract class MinecraftServerMixin {
    @Inject(method = "runServer", at = @At("HEAD"))
    private void dimtoggle$onServerStarted(CallbackInfo ci) {
        FabricDimensionControl.onServerStarted((MinecraftServer) (Object) this);
    }

    @Inject(method = "stopServer", at = @At("HEAD"))
    private void dimtoggle$onServerStopped(CallbackInfo ci) {
        FabricDimensionControl.onServerStopped();
    }

    @Inject(method = "tickChildren", at = @At("TAIL"))
    private void dimtoggle$onServerTick(BooleanSupplier hasTimeLeft, CallbackInfo ci) {
        FabricDimensionControl.tick((MinecraftServer) (Object) this);
    }
}
