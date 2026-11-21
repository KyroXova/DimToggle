package dev.kyroxova.dimtoggle.forge;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

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
