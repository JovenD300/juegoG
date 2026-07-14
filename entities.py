# entities.py
import os
import random
import math
from settings import *
import pygame




class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        ruta_base = os.path.dirname(__file__)

        # 1. CARGAR IMÁGENES: Guardamos las imágenes en un diccionario.
        # Usa .convert_alpha() para que Pygame respete el fondo transparente (PNG).
        self.sprites = {
            "up": pygame.image.load(os.path.join(ruta_base, "spaceAstronautsAR.png")).convert_alpha(),
            "down": pygame.image.load(os.path.join(ruta_base, "spaceAstronautsAB.png")).convert_alpha(),
            "left": pygame.image.load(os.path.join(ruta_base, "spaceAstronautsIZ.png")).convert_alpha(),
            "right": pygame.image.load(os.path.join(ruta_base, "spaceAstronautsDE.png")).convert_alpha()
        }
        
        # Opcional: Si tus imágenes no miden exactamente 40x40, descomenta 
        # las siguientes dos líneas para forzar su tamaño y no alterar tus colisiones:
        for key in self.sprites:
            self.sprites[key] = pygame.transform.scale(self.sprites[key], (40, 40))

        # Estado inicial
        self.current_direction = "down"
        self.image = self.sprites[self.current_direction]
        self.rect = self.image.get_rect(center=(x, y))
        
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        
        # Variables para el "Juice" (Flash de daño)
        self.damage_flash_timer = 0

    def update(self, keys, joystick):
        # Movimiento con Teclado
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += self.speed
        
        # Movimiento con Gamepad (Joystick)
        if joystick:
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)
            if abs(axis_x) > 0.1: dx += axis_x * self.speed
            if abs(axis_y) > 0.1: dy += axis_y * self.speed

        # 2. DETECTAR DIRECCIÓN: Actualizamos hacia dónde mira basado en dx y dy
        if dx > 0:
            self.current_direction = "right"
        elif dx < 0:
            self.current_direction = "left"
        elif dy > 0:
            self.current_direction = "down"
        elif dy < 0:
            self.current_direction = "up"

        # Aplicamos la imagen correspondiente a la dirección actual
        self.image = self.sprites[self.current_direction]

        self.rect.x += dx
        self.rect.y += dy

        # Límites del mundo (ejemplo: mundo de 1600x1200)
        self.rect.clamp_ip(pygame.Rect(0, 0, 1600, 1200))

        # 3. LÓGICA DEL FLASH DE DAÑO (Modificada para imágenes)
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= 1
            # Creamos una copia de la imagen actual y le superponemos color blanco
            # usando BLEND_RGB_ADD, lo que ilumina la imagen en lugar de borrarla.
            flash_image = self.image.copy()
            flash_image.fill(COLOR_WHITE, special_flags=pygame.BLEND_RGB_ADD)
            self.image = flash_image

    def take_damage(self, amount):
        self.hp -= amount
        self.damage_flash_timer = 10 # Parpadea por 10 frames


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # Usando tu método para la ruta base
        ruta_base = os.path.dirname(__file__)
        
        # 1. CARGAR IMÁGENES DEL ENEMIGO
        self.sprites = {
            "up": pygame.image.load(os.path.join(ruta_base, "EnemyAstronautsAR.png")).convert_alpha(),
            "down": pygame.image.load(os.path.join(ruta_base, "EnemyAstronautsAB.png")).convert_alpha(),
            "left": pygame.image.load(os.path.join(ruta_base, "EnemyAstronautsIZ.png")).convert_alpha(),
            "right": pygame.image.load(os.path.join(ruta_base, "EnemyAstronautsDE.png")).convert_alpha()
        }
        
        # Estado inicial
        self.current_direction = "down"
        self.image = self.sprites[self.current_direction]
        self.rect = self.image.get_rect(center=(x, y))
        
        self.speed = 2
        self.hp = 30
        self.max_hp = 30

    def update(self, player):
        # IA Básica: Perseguir al jugador
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            # Calculamos cuánto se mueve realmente en este frame
            move_x = (dx / dist) * self.speed
            move_y = (dy / dist) * self.speed
            
            self.rect.x += move_x
            self.rect.y += move_y

            # 2. DETERMINAR LA DIRECCIÓN VISUAL
            # Comparamos si el movimiento horizontal es mayor que el vertical
            if abs(move_x) > abs(move_y):
                if move_x > 0:
                    self.current_direction = "right"
                else:
                    self.current_direction = "left"
            else:
                # Si el movimiento vertical es mayor o igual
                if move_y > 0:
                    self.current_direction = "down"
                else:
                    self.current_direction = "up"
                    
            # 3. ACTUALIZAR LA IMAGEN
            self.image = self.sprites[self.current_direction]

    def draw_hp_bar(self, surface, camera_offset):
        # Barra de vida flotante (Se mantiene igual)
        pos_x = self.rect.x - camera_offset[0]
        pos_y = self.rect.y - camera_offset[1] - 10
        health_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, COLOR_WHITE, (pos_x, pos_y, 30, 5))
        pygame.draw.rect(surface, COLOR_ENEMY, (pos_x, pos_y, 30 * health_ratio, 5))

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(COLOR_UI)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 10
        
        # Calcular dirección
        angle = math.atan2(target_y - y, target_x - x)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = random.randint(4, 8)
        self.image = pygame.Surface((size, size))
        self.image.fill(COLOR_ENEMY)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = random.uniform(-4, 4)
        self.dy = random.uniform(-4, 4)
        self.lifetime = 30

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()