# main.py
import pygame
import random
import sys
import os
from settings import *
from entities import Player, Enemy, Projectile, Particle

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init() # Inicializar sistema de audio
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mi Juego 2D Profesional")
        self.clock = pygame.time.Clock()
        
        # Control de Gamepad
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        # Máquina de estados
        self.state = "MENU"
        
        self.reset_game()

    def reset_game(self):
        # Grupos de Sprites
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()

        # Instanciar Jugador
        self.player = Player(400, 300)
        self.all_sprites.add(self.player)

        # Variables de Cámara y Juice
        self.camera_x, self.camera_y = 0, 0
        self.screen_shake = 0
        self.score = 0

        self.spawn_timer = 0

    def load_assets(self):
        import os
        ruta_base = os.path.dirname(__file__)
        
        # Cargar la imagen de fondo (Asegúrate de que mida 1600x1200)
        ruta_fondo = os.path.join(ruta_base, "fondoG.png")
        self.bg_image = pygame.image.load(ruta_fondo).convert()

    def run(self):
        self.load_assets()
        while True:
            self.handle_events()
            
            if self.state == "MENU":
                self.update_menu()
                self.draw_menu()
            elif self.state == "PLAYING":
                self.update_playing()
                self.draw_playing()
            elif self.state == "GAMEOVER":
                self.update_gameover()
                self.draw_gameover()
                
            pygame.display.flip()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if self.state == "MENU":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.reset_game()
                    self.state = "PLAYING"
            
            elif self.state == "PLAYING":
                # Disparar con click del mouse
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    # Ajustar click por la posición de la cámara
                    world_x, world_y = mx + self.camera_x, my + self.camera_y
                    proj = Projectile(self.player.rect.centerx, self.player.rect.centery, world_x, world_y)
                    self.all_sprites.add(proj)
                    self.projectiles.add(proj)
                    # pygame.mixer.Sound.play(self.snd_shoot) # Ejemplo de sonido
                    
            elif self.state == "GAMEOVER":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.state = "MENU"

    def update_playing(self):
        keys = pygame.key.get_pressed()
        
        # Actualizar jugador
        self.player.update(keys, self.joystick)
        
        # Spawn de enemigos
        self.spawn_timer += 1
        if self.spawn_timer > 60: # Cada segundo
            ex = random.randint(0, 1600)
            ey = random.randint(0, 1200)
            enemy = Enemy(ex, ey)
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)
            self.spawn_timer = 0

        # Actualizar el resto
        self.enemies.update(self.player)
        self.projectiles.update()
        self.particles.update()

        # Colisiones Proyectil -> Enemigo
        hits = pygame.sprite.groupcollide(self.enemies, self.projectiles, False, True)
        for enemy, projs in hits.items():
            enemy.hp -= 10
            if enemy.hp <= 0:
                self.score += 10
                self.screen_shake = 10 # Screen shake al matar!
                # Generar partículas
                for _ in range(15):
                    p = Particle(enemy.rect.centerx, enemy.rect.centery)
                    self.all_sprites.add(p)
                    self.particles.add(p)
                enemy.kill()

        # Colisiones Enemigo -> Jugador
        if pygame.sprite.spritecollide(self.player, self.enemies, False):
            self.player.take_damage(1)
            self.screen_shake = 5
            if self.player.hp <= 0:
                self.state = "GAMEOVER"

        # Actualizar Cámara Suave (Lerp)
        target_cam_x = self.player.rect.centerx - WIDTH // 2
        target_cam_y = self.player.rect.centery - HEIGHT // 2
        self.camera_x += (target_cam_x - self.camera_x) * 0.1
        self.camera_y += (target_cam_y - self.camera_y) * 0.1

        # Reducir Screen Shake progresivamente
        if self.screen_shake > 0:
            self.screen_shake -= 1

    def draw_playing(self):
        # 1. Aplicar Screen Shake a un offset final (MANTENER IGUAL)
        shake_x = random.randint(-self.screen_shake, self.screen_shake)
        shake_y = random.randint(-self.screen_shake, self.screen_shake)
        offset_x = int(self.camera_x) + shake_x
        offset_y = int(self.camera_y) + shake_y

        # 2. DIBUJAR EL FONDO DINÁMICO
        # Borramos self.screen.fill() y los pygame.draw.circle()
        # Colocamos la imagen restando el offset para que la cámara "navegue" sobre ella
        self.screen.blit(self.bg_image, (-offset_x, -offset_y))

        # 3. Dibujar todos los sprites ajustados por la cámara (MANTENER IGUAL)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, (sprite.rect.x - offset_x, sprite.rect.y - offset_y))

        # Dibujar barras de vida flotantes de los enemigos (MANTENER IGUAL)
        for enemy in self.enemies:
            enemy.draw_hp_bar(self.screen, (offset_x, offset_y))

        # Interfaz HUD (MANTENER IGUAL)
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Puntuación: {self.score}", True, COLOR_WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Barra de Vida Jugador (MANTENER IGUAL)
        pygame.draw.rect(self.screen, COLOR_ENEMY, (10, 50, 200, 20))
        pygame.draw.rect(self.screen, COLOR_PLAYER, (10, 50, 200 * (self.player.hp / self.player.max_hp), 20))

    def update_menu(self): pass
    def draw_menu(self):
        self.screen.fill(COLOR_BG)
        font = pygame.font.SysFont(None, 72)
        text = font.render("MI JUEGO 2D", True, COLOR_UI)
        self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
        font_small = pygame.font.SysFont(None, 36)
        sub = font_small.render("Presiona ESPACIO para jugar", True, COLOR_WHITE)
        self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 50))

    def update_gameover(self): pass
    def draw_gameover(self):
        self.screen.fill(COLOR_ENEMY)
        font = pygame.font.SysFont(None, 72)
        text = font.render("GAME OVER", True, COLOR_WHITE)
        self.screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
        font_small = pygame.font.SysFont(None, 36)
        sub = font_small.render(f"Puntuación Final: {self.score} | Presiona R para reiniciar", True, COLOR_WHITE)
        self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 50))

if __name__ == "__main__":
    juego = Game()
    juego.run()