package dev.kyroxova.dimtoggle.neoforge;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.neoforge.client.event.ScreenEvent;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.Mod;

@Mod.EventBusSubscriber(modid = "dimtoggle", value = Dist.CLIENT)
public final class ClientSmokeTest {
    private ClientSmokeTest() { }

    @SubscribeEvent
    public static void screenReady(ScreenEvent.Init.Post event) {
        if (Boolean.getBoolean("dimtoggle.test.exitOnTitle") && event.getScreen() instanceof TitleScreen) {
            System.out.println("DIMTOGGLE_TEST_TITLE_SCREEN_READY");
            Minecraft.getInstance().stop();
        }
    }
}
