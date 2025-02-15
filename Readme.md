## Features

### Procedural World Generation
- The game world is procedurally generated using a seed value.
- The world is divided into chunks, each containing a grid of blocks.

### Player Mechanics
- **Movement**: The player can move left, right, and jump.
- **Gravity**: The player is affected by gravity and can fall.
- **Health, Hunger, and Thirst**: The player has health, hunger, and thirst meters that deplete over time.
- **Combat**: The player can attack using various weapons.

### Inventory System
- The player has an inventory to store items.
- Items can be added to the inventory through crafting or looting.

### Crafting System
- The player can craft items using resources collected in the world.
- A crafting UI allows the player to select and craft items.

### Mobs
- Mobs are entities that can move and interact with the world.
- Mobs have health and can drop loot when defeated.

### Console Commands
- A console allows the player to enter commands to manipulate the game state.
- Commands include setting the time of day, changing the weather, and teleporting the player.

### Day-Night Cycle
- The game features a day-night cycle with configurable durations for day and night.
- The ambient brightness changes based on the time of day.

### Weather System
- The game includes different weather types such as rain, storm, snow, and clear.
- The weather can be changed using console commands.

### Parallax Background
- The game features a parallax background that changes based on the weather.

### Lighting System
- The game includes a lighting system with light sources and ambient darkness.
- Light sources can be placed in the world to illuminate areas.

### Water Simulation
- The game includes a water simulation with flowing water.
- Water can move downward and laterally based on the terrain.

### Sound and Music
- Background music plays continuously during the game.
- Sound effects are played for actions such as jumping and attacking.

## Getting Started

### Prerequisites
- Python 3.x
- Pygame library

### Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/reriara-clone.git
    ```
2. Install the required libraries:
    ```sh
    pip install pygame
    ```

### Running the Game
1. Navigate to the project directory:
    ```sh
    cd reriara-clone
    ```
2. Run the launcher:
    ```sh
    python launcher.py
    ```

## Controls

### Movement
- **Left Arrow / A**: Move left
- **Right Arrow / D**: Move right
- **Space**: Jump

### Inventory
- **I**: Open inventory
- **1-9**: Select hotbar slot

### Crafting
- **Q**: Open crafting UI

### Console
- **~**: Toggle console
- **Enter**: Execute command
- **Up Arrow**: Previous command
- **Down Arrow**: Next command

## Console Commands

### setday
Sets the time to day.
```sh
setday
```

### setnight
Sets the time to night.
```sh
setnight
```

### setweather
Sets the weather type.
```sh
setweather <weather_type>
```

### teleport
Teleports the player to the specified coordinates.
```sh
teleport <x> <y>
```

### spawn_item
Spawns the specified item in the player's inventory.
```sh
spawn_item <item_id|item_name> <quantity>
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## License
This project is licensed under the MIT License.