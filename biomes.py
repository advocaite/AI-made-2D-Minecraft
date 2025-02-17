import noise
from block import (GRASS, DIRT, SAND, SANDSTONE, SNOW_GRASS, SNOW_DIRT,
                  SAVANNA_GRASS, SAVANNA_DIRT, LEAVESGG)  # Import blocks

class Biome:
    def __init__(self, name, surface_block, subsurface_block, 
                 temperature, humidity, height_mod=0, tree_chance=0.1,
                 tree_type="normal", grass_tint=(34, 139, 34)):
        self.name = name
        self.surface_block = surface_block
        self.subsurface_block = subsurface_block
        self.temperature = temperature
        self.humidity = humidity
        self.height_mod = height_mod  # Modify terrain height
        self.tree_chance = tree_chance
        self.tree_type = tree_type
        self.grass_tint = grass_tint

class BiomeManager:
    def __init__(self, seed):
        self.seed = seed
        self.biomes = {
            'plains': Biome('Plains', GRASS, DIRT, 
                          temperature=0.5, humidity=0.5,
                          grass_tint=(34, 139, 34)),
            
            'desert': Biome('Desert', SAND, SANDSTONE,
                          temperature=1.0, humidity=0.0,
                          height_mod=-0.2, tree_chance=0.02,
                          grass_tint=(194, 178, 128)),
            
            'savanna': Biome('Savanna', SAVANNA_GRASS, SAVANNA_DIRT,
                           temperature=0.8, humidity=0.3,
                           height_mod=0.1, tree_chance=0.05,
                           tree_type="acacia",
                           grass_tint=(169, 178, 37)),
            
            'snowy': Biome('Snowy Plains', SNOW_GRASS, SNOW_DIRT,
                         temperature=0.0, humidity=0.4,
                         height_mod=-0.1, tree_chance=0.08,
                         grass_tint=(200, 200, 200))
        }
        
        # Increase scales significantly for much larger biomes
        self.BIOME_SCALE = 500.0  # Much larger biomes (was 300)
        self.BLEND_SCALE = 1000.0   # Larger transition areas (was 50)
        
        # Reduce octaves for smoother transitions
        self.TEMPERATURE_OCTAVES = 1  # Reduced from 2
        self.HUMIDITY_OCTAVES = 1     # Reduced from 2

    def get_biome(self, x, seed_offset=0):
        # Get base temperature and humidity with larger scale
        temp = noise.pnoise1(x/self.BIOME_SCALE + self.seed + seed_offset, 
                           octaves=self.TEMPERATURE_OCTAVES,
                           persistence=0.3)  # Lower persistence for smoother changes
        
        humidity = noise.pnoise1(x/self.BIOME_SCALE + self.seed + 1000 + seed_offset,
                               octaves=self.HUMIDITY_OCTAVES,
                               persistence=0.3)
        
        # Reduce secondary noise influence for more gradual changes
        temp += 0.1 * noise.pnoise1(x/(self.BIOME_SCALE/2) + self.seed + 2000,
                                   octaves=1)
        humidity += 0.1 * noise.pnoise1(x/(self.BIOME_SCALE/2) + self.seed + 3000,
                                      octaves=1)
        
        # Normalize to 0-1 range
        temp = (temp + 1) / 2
        humidity = (humidity + 1) / 2

        # Get primary and secondary biomes based on conditions
        primary_biome = self._get_primary_biome(temp, humidity)
        secondary_biome = self._get_secondary_biome(temp, humidity)
        
        # Calculate blend factor
        blend = self.get_transition_factor(x)
        
        # Return blended biome
        return self._blend_biomes(primary_biome, secondary_biome, blend)

    def _get_primary_biome(self, temp, humidity):
        if temp < 0.2:
            return self.biomes['snowy']
        elif temp > 0.8 and humidity < 0.2:
            return self.biomes['desert']
        elif temp > 0.6 and humidity < 0.4:
            return self.biomes['savanna']
        else:
            return self.biomes['plains']

    def _get_secondary_biome(self, temp, humidity):
        # Get nearby biome for blending
        if temp < 0.3:
            return self.biomes['plains']
        elif temp > 0.7:
            return self.biomes['savanna']
        else:
            return self.biomes['plains']

    def _blend_biomes(self, biome1, biome2, blend_factor):
        """Create a new biome that blends between two biomes"""
        blend_factor = (blend_factor + 1) / 2  # Normalize to 0-1
        
        # Create new blended biome
        return Biome(
            name=f"Blend-{biome1.name}-{biome2.name}",
            surface_block=biome1.surface_block if blend_factor < 0.5 else biome2.surface_block,
            subsurface_block=biome1.subsurface_block if blend_factor < 0.5 else biome2.subsurface_block,
            temperature=biome1.temperature * (1-blend_factor) + biome2.temperature * blend_factor,
            humidity=biome1.humidity * (1-blend_factor) + biome2.humidity * blend_factor,
            height_mod=biome1.height_mod * (1-blend_factor) + biome2.height_mod * blend_factor,
            tree_chance=biome1.tree_chance * (1-blend_factor) + biome2.tree_chance * blend_factor,
            tree_type=biome1.tree_type if blend_factor < 0.5 else biome2.tree_type,
            grass_tint=self._blend_colors(biome1.grass_tint, biome2.grass_tint, blend_factor)
        )

    def _blend_colors(self, color1, color2, factor):
        """Blend two RGB colors"""
        return tuple(int(c1 * (1-factor) + c2 * factor) for c1, c2 in zip(color1, color2))

    def get_transition_factor(self, x):
        """Get smooth transition factor between biomes"""
        # Use larger scale for transitions
        return noise.pnoise1(x/self.BLEND_SCALE + self.seed + 4000, 
                           octaves=1,
                           persistence=0.3)  # Lower persistence for smoother transitions
