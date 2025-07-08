import pygame
import math
import random
import heapq

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
running = True

# Constantes
TILE_SIZE = 64
MAP_WIDTH, MAP_HEIGHT = 50, 50

# Load images
player_image = pygame.image.load('sprites/mainCharacter.png').convert_alpha()
player_image = pygame.transform.scale(player_image, (64, 64))

enemy_image = pygame.image.load('sprites/enemy.png').convert_alpha()
enemy_image = pygame.transform.scale(enemy_image, (64, 64))

powerup_image = pygame.Surface((20, 20))
powerup_image.fill((0, 255, 255))  # Power-up simples (ciano)

# Sistema de Mapa com Matriz
class TileMap:
    def __init__(self, width, height, tile_size=TILE_SIZE):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.tiles = []
        self.generate_map()
        
        self.tile_colors = {
            0: (50, 50, 50),    # Parede
            1: (100, 100, 100), # Chão
            2: (0, 100, 0),     # Grama
            3: (0, 0, 100)      # Água
        }
        
        self.tile_properties = {
            0: {"walkable": False, "speed_mod": 0},
            1: {"walkable": True, "speed_mod": 1},
            2: {"walkable": True, "speed_mod": 0.9},
            3: {"walkable": True, "speed_mod": 0.5}
        }
    
    def generate_map(self):
        for y in range(self.height):
            row = []
            for x in range(self.width):
                rand = random.random()
                if rand < 0.05:
                    row.append(0)
                elif rand < 0.15:
                    row.append(2)
                elif rand < 0.2:
                    row.append(3)
                else:
                    row.append(1)
            self.tiles.append(row)

        for y in range(5, 10):
            for x in range(5, 10):
                self.tiles[y][x] = 1
    
    def draw(self, surface, camera_x, camera_y):
        start_x = max(0, int(camera_x // self.tile_size))
        start_y = max(0, int(camera_y // self.tile_size))
        end_x = min(self.width, int((camera_x + surface.get_width()) // self.tile_size) + 1)
        end_y = min(self.height, int((camera_y + surface.get_height()) // self.tile_size) + 1)

        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_type = self.tiles[y][x]
                pygame.draw.rect(
                    surface,
                    self.tile_colors[tile_type],
                    (x * self.tile_size - camera_x, y * self.tile_size - camera_y, 
                     self.tile_size, self.tile_size)
                )
    
    def is_walkable(self, x, y):
        tile_x = int(x // self.tile_size)
        tile_y = int(y // self.tile_size)
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tile_properties[self.tiles[tile_y][tile_x]]["walkable"]
        return False
    
    def get_speed_mod(self, x, y):
        tile_x = int(x // self.tile_size)
        tile_y = int(y // self.tile_size)
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tile_properties[self.tiles[tile_y][tile_x]]["speed_mod"]
        return 1

tile_map = TileMap(MAP_WIDTH, MAP_HEIGHT)

# Player
player_x = 640
player_y = 360
player_speed = 5
player_health = 100
score = 0

# Enemies
enemy_speed = 2
enemies = []

# Bullets
bullets = []

# Spawns
enemy_spawn_timer = 0
enemy_spawn_interval = 2000
powerup_spawn_timer = 0
powerup_spawn_interval = 10000
powerups = []

# Weapons
class Weapon:
    def __init__(self, name, damage, bullet_speed, fire_pattern):
        self.name = name
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.fire_pattern = fire_pattern

    def shoot(self, player_x, player_y, mouse_x, mouse_y):
        return self.fire_pattern(player_x, player_y, mouse_x, mouse_y, self.bullet_speed)

def single_shot(x, y, mx, my, speed):
    angle = math.atan2(my - y, mx - x)
    dx = math.cos(angle) * speed
    dy = math.sin(angle) * speed
    return [[x + 32, y + 32, dx, dy, 1]]

def triple_shot(x, y, mx, my, speed):
    angle = math.atan2(my - y, mx - x)
    angles = [angle - 0.1, angle, angle + 0.1]
    return [[x + 32, y + 32, math.cos(a) * speed, math.sin(a) * speed, 1] for a in angles]

def heavy_shot(x, y, mx, my, speed):
    angle = math.atan2(my - y, mx - x)
    dx = math.cos(angle) * speed
    dy = math.sin(angle) * speed
    return [[x + 32, y + 32, dx, dy, 3]]

weapons = [
    Weapon("Pistola", 1, 10, single_shot),
    Weapon("Rifle", 3, 7, heavy_shot),
    Weapon("Shotgun", 1, 10, triple_shot)
]
current_weapon_index = 0
current_weapon = weapons[current_weapon_index]

def spawn_enemy():
    safe_distance = 200
    while True:
        x = random.randint(0, tile_map.width * tile_map.tile_size - 64)
        y = random.randint(0, tile_map.height * tile_map.tile_size - 64)
        if math.hypot(player_x - x, player_y - y) > safe_distance and tile_map.is_walkable(x, y):
            enemies.append({
                "x": x,
                "y": y,
                "path": [],
                "path_timmer": 0
            })
            break

def spawn_powerup():
    while True:
        x = random.randint(0, tile_map.width * tile_map.tile_size - 20)
        y = random.randint(0, tile_map.height * tile_map.tile_size - 20)
        if tile_map.is_walkable(x, y):
            powerups.append([x, y])
            break

camera_x = player_x - screen.get_width() // 2
camera_y = player_y - screen.get_height() // 2

def a_star(start, goal, tile_map):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            # Reconstruir o caminho
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        x, y = current
        for dx, dy in [(0,1),(1,0),(-1,0),(0,-1)]:
            neighbor = (x + dx, y + dy)
            nx, ny = neighbor
            if 0 <= nx < tile_map.width and 0 <= ny < tile_map.height:
                if not tile_map.tile_properties[tile_map.tiles[ny][nx]]["walkable"]:
                    continue
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []
# Game loop
while running:
    dt = clock.tick(60)
    screen_width, screen_height = screen.get_size()

    tile_player = (int(player_x // TILE_SIZE), int(player_y // TILE_SIZE))

    for enemy in enemies:
        ex, ey = enemy["x"], enemy["y"]
        tile_enemy = (int(ex // TILE_SIZE), int(ey // TILE_SIZE))
        
        enemy["path_timmer"] += dt

        # Recalcula o caminho se o jogador mudou de tile ou passou 1 segundo
        if ("last_player_tile" not in enemy or
            enemy["last_player_tile"] != tile_player or
            enemy["path_timmer"] > 1000 or not enemy["path"]):
            
            goal = (
                tile_player[0] + random.randint(-1, 1),
                tile_player[1] + random.randint(-1, 1)
            )
            goal = (
                max(0, min(tile_map.width - 1, goal[0])),
                max(0, min(tile_map.height - 1, goal[1]))
            )
            
            enemy["path"] = a_star(tile_enemy, goal, tile_map)
            enemy["last_player_tile"] = tile_player
            enemy["path_timmer"] = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                current_weapon_index = event.key - pygame.K_1
                current_weapon = weapons[current_weapon_index]
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_mouse_x = mouse_x + camera_x
            world_mouse_y = mouse_y + camera_y
            bullets.extend(current_weapon.shoot(player_x, player_y, world_mouse_x, world_mouse_y))

    keys = pygame.key.get_pressed()
    move_x = (keys[pygame.K_d] - keys[pygame.K_a]) * player_speed
    move_y = (keys[pygame.K_s] - keys[pygame.K_w]) * player_speed
    if move_x and move_y:
        move_x *= 0.7071
        move_y *= 0.7071
    speed_mod = tile_map.get_speed_mod(player_x, player_y)
    move_x *= speed_mod
    move_y *= speed_mod

    new_x = player_x + move_x
    new_y = player_y + move_y

    player_rect = pygame.Rect(new_x, new_y, 64, 64)
    can_move = True
    for dx in [0, 63]:
        for dy in [0, 63]:
            if not tile_map.is_walkable(new_x + dx, new_y + dy):
                can_move = False
                break
    if can_move:
        player_x, player_y = new_x, new_y

    camera_x = max(0, min(player_x - screen_width // 2, tile_map.width * TILE_SIZE - screen_width))
    camera_y = max(0, min(player_y - screen_height // 2, tile_map.height * TILE_SIZE - screen_height))

    for bullet in bullets[:]:
        bullet[0] += bullet[2]
        bullet[1] += bullet[3]
        if not (0 <= bullet[0] < tile_map.width * TILE_SIZE and
                0 <= bullet[1] < tile_map.height * TILE_SIZE and
                tile_map.is_walkable(bullet[0], bullet[1])):
            bullets.remove(bullet)

    for enemy in enemies:
        ex, ey = enemy["x"], enemy["y"]
        tile_enemy = (int(ex // TILE_SIZE), int(ey // TILE_SIZE))
        tile_player = (int(player_x // TILE_SIZE), int(player_y // TILE_SIZE))

        # Se o inimigo não tem caminho ou chegou ao final, recalcula
        if not enemy["path"] or tile_enemy == enemy["path"][-1]:
            enemy["path"] = a_star(tile_enemy, tile_player, tile_map)

        # Move no caminho
        if enemy["path"]:
            next_tile = enemy["path"][0]
            next_x = next_tile[0] * TILE_SIZE + TILE_SIZE // 2
            next_y = next_tile[1] * TILE_SIZE + TILE_SIZE // 2
            dx = next_x - ex
            dy = next_y - ey
            dist = math.hypot(dx, dy)
            if dist < 2:
                enemy["path"].pop(0)
            else:
                dx /= dist
                dy /= dist
                speed_mod = tile_map.get_speed_mod(ex, ey)
                enemy["x"] += dx * enemy_speed * speed_mod
                enemy["y"] += dy * enemy_speed * speed_mod

    # Dano ao jogador
    for enemy in enemies:
        if math.hypot(enemy["x"] - player_x, enemy["y"] - player_y) < 32:
            player_health -= 1
            if player_health <= 0:
                print(f"Game Over! Score final: {score}")
                running = False

    for bullet in bullets[:]:
        for enemy in enemies[:]:
            if math.hypot(bullet[0] - enemy["x"], bullet[1] - enemy["y"]) < 32:
                enemies.remove(enemy)
                if bullet in bullets:
                    bullets.remove(bullet)
                score += 10 * bullet[4]
                break


    for powerup in powerups[:]:
        if math.hypot(player_x - powerup[0], player_y - powerup[1]) < 32:
            powerups.remove(powerup)
            player_health = min(100, player_health + 20)

    enemy_spawn_timer += dt
    powerup_spawn_timer += dt
    if enemy_spawn_timer >= enemy_spawn_interval:
        spawn_enemy()
        enemy_spawn_timer = 0
    if powerup_spawn_timer >= powerup_spawn_interval:
        spawn_powerup()
        powerup_spawn_timer = 0

    if score < 100:
        enemy_spawn_interval = 1
    if score >= 100:
        enemy_spawn_interval = 1500
    if score >= 200:
        enemy_spawn_interval = 1000
    if score >= 300:
        enemy_spawn_interval = 800

    # Renderização
    screen.fill("black")
    tile_map.draw(screen, camera_x, camera_y)

    for powerup in powerups:
        screen.blit(powerup_image, (powerup[0] - camera_x, powerup[1] - camera_y))
    for enemy in enemies:
        screen.blit(enemy_image, (enemy["x"] - camera_x, enemy["y"] - camera_y))
    for bullet in bullets:
        pygame.draw.circle(screen, (255, 255, 0), (int(bullet[0] - camera_x), int(bullet[1] - camera_y)), 5)
    screen.blit(player_image, (player_x - camera_x, player_y - camera_y))

    # UI
    pygame.draw.rect(screen, (255, 0, 0), (10, 10, 200, 20))
    pygame.draw.rect(screen, (0, 255, 0), (10, 10, max(0, 200 * (player_health / 100)), 20))
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (10, 40))
    screen.blit(font.render(f"Arma: {current_weapon.name}", True, (255, 255, 255)), (10, 70))

    pygame.display.flip()

pygame.quit()
