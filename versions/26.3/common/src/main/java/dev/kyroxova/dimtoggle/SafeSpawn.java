package dev.kyroxova.dimtoggle;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

public final class SafeSpawn {
    private SafeSpawn() { }

    public static BlockPos find(ServerLevel level) {
        BlockPos shared = level.getRespawnData().pos();
        int minBuild = level.getMinY();
        int maxBuild = level.getMaxY();
        for (int r = 0; r <= 8; r++) {
            for (int dx = -r; dx <= r; dx++) {
                for (int dz = -r; dz <= r; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != r) continue;
                    int x = shared.getX() + dx;
                    int z = shared.getZ() + dz;
                    for (int y = maxBuild - 2; y >= minBuild + 1; y--) {
                        BlockPos pos = new BlockPos(x, y, z);
                        BlockState floor = level.getBlockState(pos.below());
                        BlockState feet = level.getBlockState(pos);
                        BlockState head = level.getBlockState(pos.above());
                        if (floor.isSolid() && feet.isAir() && head.isAir()) {
                            return pos;
                        }
                    }
                }
            }
        }
        return shared;
    }
}
