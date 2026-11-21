package dev.kyroxova.dimtoggle.fabric.mixin;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(TitleScreen.class)
public abstract class TitleScreenMixin {
    @Inject(method = "init", at = @At("RETURN"))
    private void dimtoggle$titleReady(CallbackInfo callback) {
        if (Boolean.getBoolean("dimtoggle.test.exitOnTitle")) {
            System.out.println("DIMTOGGLE_TEST_TITLE_SCREEN_READY");
            Minecraft.getInstance().stop();
        }
    }
}
