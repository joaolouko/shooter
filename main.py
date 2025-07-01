import pygame
import math
import random

# pygame setup
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
running = True

# Load images
player_image = pygame.image.load('sprites/mainCharacter.png').convert_alpha()
player_image = pygame.transform.scale(player_image, (64, 64))

enemy_image = pygame.image.load('sprites/enemy.png').convert_alpha()
enemy_image = pygame.transform.scale(enemy_image, (64, 64))

powerup_image = pygame.Surface((20, 20))
powerup_image.fill((0, 255, 255))  # Power-up simples (ciano)

# Player setup
player_x = 640
player_y = 360
player_speed = 5
player_health = 100
score = 0

# Enemy setup
enemy_speed = 2
enemies = []

# Bullet setup
bullets = []

# Spawn timers
enemy_spawn_timer = 0
enemy_spawn_interval = 2000  # 2 segundos
powerup_spawn_timer = 0
powerup_spawn_interval = 10000  # 10 segundos
powerups = []

# Sistema de armas
class Weapon:
    def __init__(self, name, damage, bullet_speed, fire_pattern):
        self.name = name
        self.damage = damage
        self.bullet_speed = bullet_speed
        self.fire_pattern = fire_pattern

    def shoot(self, player_x, player_y, mouse_x, mouse_y):
        return self.fire_pattern(player_x, player_y, mouse_x, mouse_y, self.bullet_speed)

# Padrões de tiro
def single_shot(x, y, mx, my, speed):
    angle = math.atan2(my - y, mx - x)
    dx = math.cos(angle) * speed
    dy = math.sin(angle) * speed
    return [[x + 32, y + 32, dx, dy, 1]]

def triple_shot(x, y, mx, my, speed):
    angle = math.atan2(my - y, mx - x)
    angles = [angle - 0.1, angle, angle + 0.1]
    bullets = []
    for a in angles:
        dx = math.cos(a) * speed
        dy = math.sin(a) * speed
        bullets.append([x + 32, y + 32, dx, dy, 1])
    return bullets

def heavy_shot(x, y, mx, my, speed):
    angle = math.atan2(my - y, mx - x)
    dx = math.cos(angle) * speed
    dy = math.sin(angle) * speed
    return [[x + 32, y + 32, dx, dy, 3]]

# Armas disponíveis
weapons = [
    Weapon("Pistola", 1, 10, single_shot),
    Weapon("Rifle", 3, 7, heavy_shot),
    Weapon("Shotgun", 1, 10, triple_shot)
]
current_weapon_index = 0
current_weapon = weapons[current_weapon_index]

# Funções de spawn
def spawn_enemy():
    safe_distance = 200
    while True:
        x = random.randint(0, 1280 - 64)
        y = random.randint(0, 720 - 64)
        if math.hypot(player_x - x, player_y - y) > safe_distance:
            enemies.append([x, y])
            break

def spawn_powerup():
    x = random.randint(0, 1280 - 20)
    y = random.randint(0, 720 - 20)
    powerups.append([x, y])

# Game loop
while running:
    dt = clock.tick(60)
    screen_width = 1280
    screen_height = 720

    # Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                current_weapon_index = 0
            if event.key == pygame.K_2:
                current_weapon_index = 1
            if event.key == pygame.K_3:
                current_weapon_index = 2
            current_weapon = weapons[current_weapon_index]

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            new_bullets = current_weapon.shoot(player_x, player_y, mouse_x, mouse_y)
            bullets.extend(new_bullets)

    # Movimento do player
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_y -= player_speed
    if keys[pygame.K_s]:
        player_y += player_speed
    if keys[pygame.K_a]:
        player_x -= player_speed
    if keys[pygame.K_d]:
        player_x += player_speed

    # Wrap do player
    if player_x > screen_width:
        player_x = -player_image.get_width()
    elif player_x < -player_image.get_width():
        player_x = screen_width
    if player_y > screen_height:
        player_y = -player_image.get_height()
    elif player_y < -player_image.get_height():
        player_y = screen_height

    # Atualizar balas
    for bullet in bullets[:]:
        bullet[0] += bullet[2]
        bullet[1] += bullet[3]
        if bullet[0] < 0 or bullet[0] > screen_width or bullet[1] < 0 or bullet[1] > screen_height:
            bullets.remove(bullet)

    # Movimento e colisão inimigos
    for enemy_pos in enemies[:]:
        dx = player_x - enemy_pos[0]
        dy = player_y - enemy_pos[1]
        distance = math.hypot(dx, dy)
        if distance != 0:
            enemy_pos[0] += (dx / distance) * enemy_speed
            enemy_pos[1] += (dy / distance) * enemy_speed
        if distance < 32:
            player_health -= 1
            if player_health <= 0:
                print(f"Game Over! Score final: {score}")
                running = False

    # Colisão bala-inimigo
    for bullet in bullets[:]:
        for enemy_pos in enemies[:]:
            if math.hypot(bullet[0] - enemy_pos[0], bullet[1] - enemy_pos[1]) < 32:
                enemies.remove(enemy_pos)
                if bullet in bullets:
                    bullets.remove(bullet)
                score += 10 * bullet[4]
                break

    # Colisão power-up
    for powerup in powerups[:]:
        if math.hypot(player_x - powerup[0], player_y - powerup[1]) < 32:
            powerups.remove(powerup)
            player_health = min(100, player_health + 20)

    # Spawn inimigo/powerup
    enemy_spawn_timer += dt
    powerup_spawn_timer += dt
    if enemy_spawn_timer >= enemy_spawn_interval:
        spawn_enemy()
        enemy_spawn_timer = 0
    if powerup_spawn_timer >= powerup_spawn_interval:
        spawn_powerup()
        powerup_spawn_timer = 0

    # Dificuldade dinâmica
    if score >= 100:
        enemy_spawn_interval = 1500
    if score >= 200:
        enemy_spawn_interval = 1000
    if score >= 300:
        enemy_spawn_interval = 800

    # Renderização
    screen.fill("purple")
    screen.blit(player_image, (player_x, player_y))
    for enemy_pos in enemies:
        screen.blit(enemy_image, (enemy_pos[0], enemy_pos[1]))
    for bullet in bullets:
        pygame.draw.circle(screen, (255, 255, 0), (int(bullet[0]), int(bullet[1])), 5)
    for powerup in powerups:
        screen.blit(powerup_image, (powerup[0], powerup[1]))

    pygame.draw.rect(screen, (255, 0, 0), (10, 10, 200, 20))
    pygame.draw.rect(screen, (0, 255, 0), (10, 10, max(0, 200 * (player_health / 100)), 20))

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    weapon_text = font.render(f"Arma: {current_weapon.name}", True, (255, 255, 255))
    screen.blit(score_text, (10, 40))
    screen.blit(weapon_text, (10, 70))

    pygame.display.flip()

pygame.quit()
