import arcade
import sys
import os
import random
import math
from drawing_second_room_first_lvl import MyGame

def setup_game(width=1200, height=675, title="Texture"):
    game = MyGame(width, height, title)
    game.setup()
    return game


def main():
    game = setup_game()
    arcade.run()

# Добавляем путь к корневой папке проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
TITLE = "Texture"

# Константы для персонажа
PLAYER_SCALING = 0.6
PLAYER_MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 17
GRAVITY = 1
PLAYER_MAX_HP = 100

# Константы для камеры - УМЕНЬШЕНЫ В 2 РАЗА
CAMERA_LERP = 0.12
DEAD_ZONE_W = int(SCREEN_WIDTH * 0.35 / 3)  # Уменьшено в 2 раза
DEAD_ZONE_H = int(SCREEN_HEIGHT * 0.45 / 3)  # Уменьшено в 2 раза

# Константы для рывка
DASH_SPEED = 30
DASH_DURATION = 0.3
DASH_COOLDOWN = 1.0

# Константы для гейзера
GEYSER_DAMAGE = 30  # 30% урона
GEYSER_ACTIVE_DURATION = 1.5  # Секунд активности
GEYSER_COOLDOWN_DURATION = 3.0  # Секунд перерыва
GEYSER_WIDTH = 100
GEYSER_HEIGHT = 65
GEYSER_BLAST_SPEED = 15  # Скорость подбрасывания


class DustParticle(arcade.SpriteCircle):
    """Частица пыли для эффекта приземления"""

    def __init__(self, x, y):
        color = random.choice([
            (200, 200, 200, 200),
            (180, 180, 180, 200),
            (220, 220, 220, 200),
            (190, 170, 150, 200)
        ])
        size = random.randint(3, 8)
        super().__init__(size, color)
        self.center_x = x
        self.center_y = y
        self.change_x = random.uniform(-1.5, 1.5)
        self.change_y = random.uniform(0, 2)

        # Начальные параметры согласно ТЗ
        self.scale = 1.0
        self.alpha = 200
        self.lifetime = random.uniform(0.5, 1.2)
        self.time_alive = 0

    def update(self, delta_time=1 / 60):
        # Движение частицы
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Замедление
        self.change_x *= 0.95
        self.change_y *= 0.95

        # Изменение масштаба по ТЗ: по X 1.02, по Y 1.005
        self.width *= 1.02
        self.height *= 1.005

        # Уменьшение прозрачности
        if self.alpha > 2:
            self.alpha -= 2

        # Увеличение времени жизни
        self.time_alive += delta_time

        # Проверка на окончание времени жизни
        if self.time_alive > self.lifetime or self.alpha <= 0:
            self.remove_from_sprite_lists()


class GeyserEffect(arcade.SpriteCircle):
    """Частица эффекта гейзера"""

    def __init__(self, x, y):
        # Цвета гейзера (сине-голубые оттенки)
        color = random.choice([
            (100, 150, 255, 180),  # Голубой
            (80, 180, 255, 200),  # Светло-голубой
            (150, 200, 255, 150),  # Очень светлый голубой
            (200, 220, 255, 120),  # Почти белый с синим оттенком
            (255, 255, 255, 255)
        ])
        size = random.randint(4, 12)
        super().__init__(size, color)
        self.center_x = x + random.uniform(-GEYSER_WIDTH // 3, GEYSER_WIDTH // 3)
        self.center_y = y
        self.change_x = random.uniform(-0.5, 0.5)
        self.change_y = random.uniform(8, 12)

        self.scale = 1.0
        self.alpha = random.randint(150, 255)
        self.lifetime = random.uniform(0.8, 1.5)
        self.time_alive = 0
        self.gravity = 0.3

    def update(self, delta_time=1 / 60):
        # Движение частицы
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Гравитация
        self.change_y -= self.gravity

        # Замедление по горизонтали
        self.change_x *= 0.98

        # Уменьшение размера по обеим осям
        self.scale = (self.scale[0] * 0.98, self.scale[1] * 0.98)

        # Уменьшение прозрачности
        if self.alpha > 3:
            self.alpha -= 3

        # Увеличение времени жизни
        self.time_alive += delta_time

        # Проверка на окончание времени жизни
        if self.time_alive > self.lifetime or self.alpha <= 0:
            self.remove_from_sprite_lists()


class Geyser(arcade.Sprite):
    """Гейзер, наносящий урон игроку"""

    def __init__(self, x, y):
        super().__init__()
        self.texture = arcade.load_texture("first_room/images/geyser.png")
        self.center_x = x
        self.center_y = y
        self.width = GEYSER_WIDTH
        self.height = GEYSER_HEIGHT

        # Состояние гейзера
        self.active = False
        self.timer = 0
        self.cycle_time = 0

        # Эффекты
        self.effects = arcade.SpriteList()

        # Зона урона (прямоугольник)
        self.hitbox_left = x - GEYSER_WIDTH // 2
        self.hitbox_right = x + GEYSER_WIDTH // 2
        self.hitbox_bottom = y
        self.hitbox_top = y + GEYSER_HEIGHT

        # Флаг для отслеживания уже нанесенного урона в текущем цикле
        self.damage_dealt_in_current_cycle = False

        # Спрайт для коллизии (платформа)
        self.platform_sprite = arcade.Sprite()
        self.platform_sprite.texture = self.texture
        self.platform_sprite.center_x = self.center_x
        self.platform_sprite.center_y = self.center_y - self.height // 2 + 5
        self.platform_sprite.width = self.width
        self.platform_sprite.height = 10

    def update(self, delta_time):
        # Обновляем таймер цикла
        self.cycle_time += delta_time

        # Определяем состояние гейзера
        cycle_duration = GEYSER_ACTIVE_DURATION + GEYSER_COOLDOWN_DURATION
        cycle_position = self.cycle_time % cycle_duration

        old_active = self.active
        self.active = (cycle_position < GEYSER_ACTIVE_DURATION)

        # Сбрасываем флаг урона при переходе из неактивного в активное состояние
        if not old_active and self.active:
            self.damage_dealt_in_current_cycle = False

        # Обновляем таймер активности/неактивности
        if self.active:
            self.timer = GEYSER_ACTIVE_DURATION - (GEYSER_ACTIVE_DURATION - cycle_position)

            # Создаем частицы эффекта только когда активен
            if random.random() < 0.7:  # 70% шанс создать частицу каждый кадр
                effect = GeyserEffect(self.center_x, self.hitbox_bottom)
                self.effects.append(effect)
        else:
            self.timer = 0

        # Обновляем частицы эффектов
        self.effects.update(delta_time)

    def draw(self):
        """Отрисовывает гейзер и его эффекты"""
        # Отрисовываем эффекты (только когда есть частицы)
        if self.active:
            self.effects.draw()

        # Отрисовываем сам гейзер (всегда без прозрачности)
        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(
            self.center_x,
            self.center_y,
            self.width,
            self.height)
        )

        # Для отладки: отрисовываем хитбокс
        # if self.active:
        #     arcade.draw_rectangle_outline(
        #         self.center_x,
        #         (self.hitbox_bottom + self.hitbox_top) / 2,
        #         self.width,
        #         self.height,
        #         arcade.color.RED,
        #         2
        #     )

    def check_collision(self, player):
        """Проверяет столкновение с игроком и наносит урон"""
        if not self.active or self.damage_dealt_in_current_cycle:
            return False

        # Проверяем пересечение с хитбоксом гейзера
        player_hitbox = (
            player.left,
            player.right,
            player.bottom,
            player.top
        )

        geyer_hitbox = (
            self.hitbox_left,
            self.hitbox_right,
            self.hitbox_bottom,
            self.hitbox_top
        )

        # Проверка пересечения прямоугольников
        collision = not (
                player_hitbox[1] < geyer_hitbox[0] or  # player.right < geyser.left
                player_hitbox[0] > geyer_hitbox[1] or  # player.left > geyser.right
                player_hitbox[2] > geyer_hitbox[3] or  # player.bottom > geyser.top
                player_hitbox[3] < geyer_hitbox[2]  # player.top < geyser.bottom
        )

        if collision:
            self.damage_dealt_in_current_cycle = True
            return True

        return False

    def apply_blast(self, player):
        """Применяет эффект подбрасывания игрока"""
        if self.active:
            # Подбрасываем игрока вверх
            player.change_y = GEYSER_BLAST_SPEED
            # Слегка сносит в сторону от центра гейзера
            if player.center_x < self.center_x:
                player.change_x = -5
            else:
                player.change_x = 5


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()
        # Загружаем текстуры лягушки
        self.idle_texture = arcade.load_texture(":resources:images/enemies/frog.png")
        self.jump_texture = arcade.load_texture(":resources:images/enemies/frog_move.png")

        self.texture = self.idle_texture
        self.scale = PLAYER_SCALING
        self.center_x = 0
        self.center_y = 100
        self.change_x = 0
        self.change_y = 0

        # HP игрока
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.invincible_timer = 0  # Таймер неуязвимости после получения урона
        self.invincible_duration = 1.0  # 1 секунда неуязвимости

        self.on_ground = False
        self.jumping = False
        self.was_jumping = False

        # Переменные для рывка
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_direction = 1
        self.normal_speed = PLAYER_MOVEMENT_SPEED

    def update_texture(self):
        """Обновляет текстуру в зависимости от состояния"""
        if not self.on_ground:
            self.texture = self.jump_texture
        else:
            self.texture = self.idle_texture

    def take_damage(self, damage_percent):
        """Наносит урон в процентах от максимального HP"""
        if self.invincible_timer <= 0:
            damage = self.max_hp * (damage_percent / 100)
            self.hp = max(0, self.hp - damage)
            self.invincible_timer = self.invincible_duration
            return True
        return False

    def heal(self, heal_amount):
        """Восстанавливает HP"""
        self.hp = min(self.max_hp, self.hp + heal_amount)

    def update(self, delta_time):
        """Обновляет состояние игрока"""
        # Обновляем таймер неуязвимости
        if self.invincible_timer > 0:
            self.invincible_timer -= delta_time

        # Мигание при неуязвимости
        if self.invincible_timer > 0:
            self.alpha = 150 + int(105 * math.sin(self.invincible_timer * 20))
        else:
            self.alpha = 255


class GameWindow(arcade.Window):
    """Основное игровое окно"""

    def __init__(self, level=1):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, antialiasing=True)
        self.w = SCREEN_WIDTH * 2
        self.h = SCREEN_HEIGHT * 2
        self.filename = "images/background.png"
        self.level = level  # Текущий уровень

        # Камера на весь экран
        self.world_camera = arcade.camera.Camera2D(
            viewport=arcade.rect.LRBT(
                left=0,
                right=SCREEN_WIDTH,
                bottom=0,
                top=SCREEN_HEIGHT
            )
        )

        # GUI камера для интерфейса (весь экран)
        self.gui_camera = arcade.camera.Camera2D(
            viewport=arcade.rect.LRBT(
                left=0,
                right=SCREEN_WIDTH,
                bottom=0,
                top=SCREEN_HEIGHT
            )
        )

        # Игровые объекты
        self.player = None
        self.platforms = None
        self.walls = None
        self.spikes = None
        self.trampolines = None
        self.background_platforms = None
        self.dust_particles = None  # Частицы пыли
        self.geysers = None  # Список гейзеров

        # Текст для отображения кулдауна рывка и HP
        self.dash_cooldown_text = None
        self.hp_text = None

        # Физический движок
        self.physics_engine = None

        # Таймер для обновления
        self.update_time = 0

        # Границы уровня для камеры
        self.level_left = 0
        self.level_right = self.w  # Ширина мира
        self.level_bottom = 0
        self.level_top = self.h  # Высота мира

        # Переменные для камеры
        self.camera_target_x = 0
        self.camera_target_y = 0

        self.setup()

    def setup(self):
        # Загружаем текстуры из папки first_room/images
        self.texture = arcade.load_texture("first_room/images/background.png")
        self.big_platform = arcade.load_texture("first_room/images/platform1.png")
        self.small_platform = arcade.load_texture("first_room/images/platform3.png")
        self.gray_platform = arcade.load_texture("first_room/images/platform2.png")
        self.platform = arcade.load_texture("first_room/images/platform4.png")
        self.spike_texture = arcade.load_texture("first_room/images/spikes.png")
        self.wall_texture = arcade.load_texture("first_room/images/wall.png")
        self.trampoline_texture = arcade.load_texture("first_room/images/trampoline.png")
        self.falling_lava_texture = arcade.load_texture('first_room/images/falling_lava.png')
        self.geyser_texture = arcade.load_texture("first_room/images/geyser.png")

        # Создаем группы спрайтов
        self.platforms = arcade.SpriteList()
        self.walls = arcade.SpriteList()
        self.spikes = arcade.SpriteList()
        self.trampolines = arcade.SpriteList()
        self.background_platforms = arcade.SpriteList()
        self.dust_particles = arcade.SpriteList()  # Инициализируем список частиц
        self.geysers = arcade.SpriteList()  # Инициализируем список гейзеров

        # Создаем текст для отображения кулдауна и HP
        self.dash_cooldown_text = arcade.Text(
            "",
            0, 0,
            arcade.color.RED,
            12,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )

        self.hp_text = arcade.Text(
            "",
            0, 0,
            arcade.color.GREEN,
            16,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )

        # Создаем игрока
        self.player = Player()

        # Создаем платформы (для разных уровней можно будет менять)
        self.create_platforms()

        # Создаем гейзеры
        geyser_x = 280 * 2  # 560
        geyser_y = 1365
        geyser1 = Geyser(geyser_x, geyser_y)
        self.geysers.append(geyser1)

        geyser_x = 870 * 2  # 1740
        geyser_y = 1315
        geyser2 = Geyser(geyser_x, geyser_y)
        self.geysers.append(geyser2)

        # Добавляем платформы гейзеров в список платформ для коллизий
        for geyser in self.geysers:
            self.platforms.append(geyser.platform_sprite)
            self.background_platforms.append(geyser.platform_sprite)

        # Создаем физический движок
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            self.platforms,
            gravity_constant=GRAVITY
        )

        # Устанавливаем начальную позицию камеры на игрока
        self.world_camera.position = (self.player.center_x, self.player.center_y)
        self.camera_target_x = self.player.center_x
        self.camera_target_y = self.player.center_y

    def create_dust_effect(self):
        """Создаёт эффект пыли при приземлении"""
        for _ in range(random.randint(15, 20)):
            particle = DustParticle(self.player.center_x, self.player.bottom)
            self.dust_particles.append(particle)

    def create_platforms(self):
        floor_segments = 10
        segment_width = self.w / floor_segments
        segment_height = 160

        texture = self.platform

        floor_segment = arcade.Sprite()
        floor_segment.texture = texture
        floor_segment.center_x = segment_width / 2
        floor_segment.center_y = 51
        floor_segment.width = 1800
        floor_segment.height = 800
        self.platforms.append(floor_segment)
        self.background_platforms.append(floor_segment)

        # Шипы на полу
        xx = 50
        for i in range(47):
            lava = arcade.Sprite()
            lava.texture = arcade.load_texture("first_room/images/falling_lava.png")
            lava.center_x = self.w // 7 + xx + 5
            lava.center_y = 42
            lava.width = 660
            lava.height = 30
            self.spikes.append(lava)
            xx += 60

        platforms_data = [
            (280, (92 - 28) * 2, self.small_platform, 2000, 800, True),
            (420, 92 * 2, self.small_platform, 2000, 800, True),
            (560, 240, self.small_platform, 2000, 800, True),
            (820, 148 * 2, self.big_platform, 400, 100, True),
            (640, 258 * 2, self.platform, 1600, 600, True),
            (820, 368 * 2, self.big_platform, 400, 100, True),
            (1040, 368 * 2, self.platform, 1600, 600, True),
            (720 * 2, 600, self.big_platform, 400, 100, True),
            (830 * 2, 600, self.platform, 1600, 600, True),
            (920 * 2, 600, self.big_platform, 400, 100, True),
            (1040 * 2, 600, self.big_platform, 400, 100, True),
            (1340 * 2, 370 * 2, self.platform, 1600, 600, True),
            (285 * 2, 860, self.small_platform, 2000, 800, True),
            (85 * 2, 980, self.platform, 1600, 600, True),
            (15 * 2, 1100, self.small_platform, 2000, 800, True),
            (103 * 2, 1220, self.small_platform, 2000, 800, True),
            (280 * 2, 1340, self.big_platform, 400, 100, True),
            (530 * 2, 1290, self.big_platform, 400, 100, True),
            (665 * 2, 1100, self.small_platform, 2000, 800, True),
            (800 * 2, 1290, self.big_platform, 400, 100, True),
            (940 * 2, 1290, self.big_platform, 400, 100, True),
            (2150, 1410, self.platform, 1600, 600, True),
            (2150, 1430, self.small_platform, 2000, 800, True),
        ]

        for x, y, texture, width, height, add_collision in platforms_data:
            platform = arcade.Sprite()
            platform.texture = texture
            platform.center_x = x
            platform.center_y = y
            platform.width = width
            platform.height = height
            if add_collision:
                self.platforms.append(platform)
            self.background_platforms.append(platform)

        # Дополнительные шипы
        spike_locations = [
            (850, 386 * 2 - 1),
            (1050, 386 * 2 - 1),
        ]

        for x, y in spike_locations:
            spike = arcade.Sprite()
            spike.texture = self.spike_texture
            spike.center_x = x
            spike.center_y = y
            spike.width = 90
            spike.height = 37
            self.spikes.append(spike)

        # Батуты
        trampoline_locations = [
            (460 * 2, 171 * 2, 80 * 2, 45 * 2),
            (285 * 2, 281 * 2, 80 * 2, 45 * 2),
            (2150, 1485, 160, 90)
        ]

        for x, y, width, height in trampoline_locations:
            # Визуальная часть батута
            trampoline = arcade.Sprite()
            trampoline.texture = self.trampoline_texture
            trampoline.center_x = x
            trampoline.center_y = y
            trampoline.width = width
            trampoline.height = height
            self.trampolines.append(trampoline)

            # Платформа для хождения
            tramp_platform = arcade.Sprite()
            tramp_platform.texture = self.platform
            tramp_platform.center_x = x
            tramp_platform.center_y = y - height // 2 + 5
            tramp_platform.width = width
            tramp_platform.height = 10
            self.platforms.append(tramp_platform)
            self.background_platforms.append(tramp_platform)

        # Стены и потолок
        wall_size = 40

        # Левая стена
        wall_y = 20 + 40 + wall_size * 3
        wall_x = wall_size // 2

        while wall_y < self.h:
            # Визуальная часть стены
            wall = arcade.Sprite()
            wall.texture = self.wall_texture
            wall.center_x = wall_x
            wall.center_y = wall_y
            wall.width = wall_size
            wall.height = wall_size
            self.walls.append(wall)

            # Коллизионная часть стены
            wall_platform = arcade.Sprite()
            wall_platform.texture = self.wall_texture
            wall_platform.center_x = wall_x
            wall_platform.center_y = wall_y
            wall_platform.width = wall_size
            wall_platform.height = wall_size
            self.platforms.append(wall_platform)
            wall_y += wall_size

        # Правая стена (с проходом)
        wall_start_y = 20 + 40
        wall_height_available = self.h - wall_start_y
        middle_height = wall_start_y + wall_height_available // 2
        exit_start_y = middle_height + wall_size
        exit_end_y = exit_start_y + wall_size * 3

        wall_y = wall_start_y
        wall_x = self.w - wall_size // 2

        while wall_y < self.h:
            if not (exit_start_y <= wall_y < exit_end_y):
                # Визуальная часть стены
                wall = arcade.Sprite()
                wall.texture = self.wall_texture
                wall.center_x = wall_x
                wall.center_y = wall_y
                wall.width = wall_size
                wall.height = wall_size
                self.walls.append(wall)

                # Коллизионная часть стены
                wall_platform = arcade.Sprite()
                wall_platform.texture = self.wall_texture
                wall_platform.center_x = wall_x
                wall_platform.center_y = wall_y
                wall_platform.width = wall_size
                wall_platform.height = wall_size
                self.platforms.append(wall_platform)
            wall_y += wall_size

        # Потолок
        ceiling_y = self.h - wall_size // 2
        ceiling_x = wall_size // 2

        # Координаты самого высокого трамплина
        highest_trampoline_x = 2150
        highest_trampoline_y = 1460
        highest_trampoline_width = 160

        # Вычисляем область потолка, которую нужно убрать (над трамплином)
        trampoline_left = highest_trampoline_x - highest_trampoline_width // 2
        trampoline_right = highest_trampoline_x + highest_trampoline_width // 2

        # Увеличиваем область пропуска для надежности
        gap_left = trampoline_left - wall_size * 1.5
        gap_right = trampoline_right + wall_size * 1.5

        while ceiling_x < self.w:
            # Пропускаем 3 прямоугольника (плитки) прямо над трамплином
            if gap_left <= ceiling_x <= gap_right:
                # Не создаем плитку потолка в этой области
                ceiling_x += wall_size
                continue

            # Визуальная часть потолка
            ceiling = arcade.Sprite()
            ceiling.texture = self.wall_texture
            ceiling.center_x = ceiling_x
            ceiling.center_y = ceiling_y
            ceiling.width = wall_size
            ceiling.height = wall_size
            self.walls.append(ceiling)

            # Коллизионная часть потолка
            ceiling_platform = arcade.Sprite()
            ceiling_platform.texture = self.wall_texture
            ceiling_platform.center_x = ceiling_x
            ceiling_platform.center_y = ceiling_y
            ceiling_platform.width = wall_size
            ceiling_platform.height = wall_size
            self.platforms.append(ceiling_platform)
            ceiling_x += wall_size

    def on_draw(self):
        self.clear()

        # Используем мировую камеру для отрисовки игровых объектов
        self.world_camera.use()

        # Отрисовываем фон
        arcade.draw_texture_rect(
            self.texture,
            arcade.rect.XYWH(
                self.w // 2,  # Центрируем фон
                self.h // 2,
                self.w,
                self.h
            )
        )

        # Отрисовываем все игровые объекты
        self.background_platforms.draw()
        self.walls.draw()
        self.spikes.draw()
        self.trampolines.draw()
        self.dust_particles.draw()  # Отрисовываем частицы

        # Отрисовываем гейзеры
        for geyser in self.geysers:
            geyser.draw()

        # Отрисовываем игрока
        arcade.draw_texture_rect(
            self.player.texture,
            arcade.rect.XYWH(
                self.player.center_x,
                self.player.center_y,
                self.player.width,
                self.player.height
            )
        )

        # Переключаемся на GUI камеру для интерфейса
        self.gui_camera.use()

        # Отображаем информацию о рывке
        if self.player.dash_cooldown_timer > 0:
            cooldown_percent = self.player.dash_cooldown_timer / DASH_COOLDOWN
            self.dash_cooldown_text.text = f"Dash: {cooldown_percent * 100:.0f}%"
            # Позиция текста относительно GUI камеры
            self.dash_cooldown_text.x = SCREEN_WIDTH // 2
            self.dash_cooldown_text.y = SCREEN_HEIGHT - 50
            self.dash_cooldown_text.draw()

        # Отображаем HP игрока
        hp_color = arcade.color.GREEN
        if self.player.hp < 30:
            hp_color = arcade.color.RED
        elif self.player.hp < 60:
            hp_color = arcade.color.YELLOW

        self.hp_text.text = f"HP: {int(self.player.hp)}/{self.player.max_hp}"
        self.hp_text.color = hp_color
        self.hp_text.x = 100
        self.hp_text.y = SCREEN_HEIGHT - 50
        self.hp_text.draw()

        # Полоска HP
        hp_width = 200
        hp_height = 20
        hp_x = 100
        hp_y = SCREEN_HEIGHT - 80

        # Фон полоски HP
        arcade.draw_rect_filled(arcade.rect.XYWH(
            hp_x, hp_y,
            hp_width, hp_height),
            arcade.color.BLACK
        )

        # Текущее HP
        hp_percentage = self.player.hp / self.player.max_hp
        current_hp_width = hp_width * hp_percentage

        arcade.draw_rect_filled(arcade.rect.XYWH(
            hp_x - (hp_width - current_hp_width) / 2, hp_y,
            current_hp_width, hp_height),
            hp_color
        )

        # Рамка полоски HP
        arcade.draw_rect_outline(arcade.rect.XYWH(
            hp_x, hp_y,
            hp_width, hp_height),
            arcade.color.WHITE, 2
        )

    def on_update(self, delta_time):
        if self.player.center_y > SCREEN_HEIGHT:
            main()

        # Сохраняем время для обновления таймеров
        self.update_time = delta_time

        # Обновляем таймеры рывка
        if self.player.dashing:
            self.player.dash_timer -= delta_time
            if self.player.dash_timer <= 0:
                self.player.dashing = False
                if abs(self.player.change_x) > PLAYER_MOVEMENT_SPEED:
                    self.player.change_x = self.player.normal_speed * (1 if self.player.change_x > 0 else -1)

        # Обновляем кулдаун рывка
        if self.player.dash_cooldown_timer > 0:
            self.player.dash_cooldown_timer -= delta_time

        # Обновляем игрока
        self.player.update(delta_time)

        # Обновляем гейзеры
        for geyser in self.geysers:
            geyser.update(delta_time)

            # Проверяем столкновение с гейзером только когда он активен
            if geyser.active and geyser.check_collision(self.player):
                damage_taken = self.player.take_damage(GEYSER_DAMAGE)
                if damage_taken:
                    # Применяем эффект подбрасывания
                    geyser.apply_blast(self.player)

                    # Проверяем смерть игрока
                    if self.player.hp <= 0:
                        self.reset_player()

        # Обновляем физический движок
        self.physics_engine.update()

        # Обновляем частицы пыли
        self.dust_particles.update(delta_time)

        # Проверяем столкновение с шипами
        spike_hit_list = arcade.check_for_collision_with_list(self.player, self.spikes)
        if spike_hit_list:
            self.reset_player()

        # Проверяем столкновение с батутами
        trampoline_hit_list = arcade.check_for_collision_with_list(self.player, self.trampolines)
        if trampoline_hit_list and self.player.change_y < 0:
            self.player.change_y = PLAYER_JUMP_SPEED * 1.5

        # Проверяем, находится ли игрок на земле
        was_on_ground = self.player.on_ground
        self.player.on_ground = self.physics_engine.can_jump()

        # Обновляем текстуру игрока в зависимости от состояния
        self.player.update_texture()

        # Логика поворота лягушки (как в примере)
        if self.player.change_x > 0:
            # Исходная текстура лягушки смотрит влево, поэтому для движения вправо зеркалим
            self.player.scale_x = -0.6
        elif self.player.change_x < 0:
            self.player.scale_x = 0.6

        # Проверяем момент приземления для создания эффекта пыли
        if was_on_ground == False and self.player.on_ground == True:
            self.create_dust_effect()

        # Обновляем флаг для отслеживания прыжка
        if not self.player.on_ground:
            self.player.was_jumping = True
        elif self.player.was_jumping:
            self.player.was_jumping = False

        # Ограничиваем игрока в пределах мира по горизонтали
        if self.player.left < 0:
            self.player.left = 0
        if self.player.right > self.w:
            self.player.right = self.w

        # Проверяем выпадение за нижнюю границу
        if self.player.bottom < -100:
            self.reset_player()

        # Обновляем позицию камеры
        self.update_camera_position(delta_time)

    def reset_player(self):
        """Сбрасывает позицию игрока и его состояние"""
        self.player.center_x = 0
        self.player.center_y = 100
        self.player.change_x = 0
        self.player.change_y = 0
        self.player.hp = PLAYER_MAX_HP  # Восстанавливаем HP

        # Сбрасываем состояние рывка
        self.player.dashing = False
        self.player.dash_timer = 0
        self.player.dash_cooldown_timer = 0

        # Сбрасываем таймер неуязвимости
        self.player.invincible_timer = 0

        # Сбрасываем камеру
        self.world_camera.position = (self.player.center_x, self.player.center_y)

    def update_camera_position(self, delta_time):
        """Обновляет позицию камеры с учетом dead zone"""
        cam_x, cam_y = self.world_camera.position
        px, py = self.player.center_x, self.player.center_y

        # Определяем dead zone относительно текущей позиции камеры
        dz_left = cam_x - DEAD_ZONE_W // 2
        dz_right = cam_x + DEAD_ZONE_W // 2
        dz_bottom = cam_y - DEAD_ZONE_H // 2
        dz_top = cam_y + DEAD_ZONE_H // 2

        # Проверяем, находится ли игрок в dead zone
        player_in_dz = (
                px >= dz_left and
                px <= dz_right and
                py >= dz_bottom and
                py <= dz_top
        )

        # Если игрок вне dead zone, перемещаем камеру
        if not player_in_dz:
            # Вычисляем смещение для центрирования игрока
            if px < dz_left:
                self.camera_target_x = px + DEAD_ZONE_W // 2
            elif px > dz_right:
                self.camera_target_x = px - DEAD_ZONE_W // 2
            else:
                self.camera_target_x = cam_x

            if py < dz_bottom:
                self.camera_target_y = py + DEAD_ZONE_H // 2
            elif py > dz_top:
                self.camera_target_y = py - DEAD_ZONE_H // 2
            else:
                self.camera_target_y = cam_y
        else:
            # Игрок в dead zone - оставляем цель камеры как есть
            self.camera_target_x = cam_x
            self.camera_target_y = cam_y

        # Ограничиваем позицию камеры границами уровня
        half_viewport_w = SCREEN_WIDTH // 2
        half_viewport_h = SCREEN_HEIGHT // 2

        min_camera_x = self.level_left + half_viewport_w
        max_camera_x = self.level_right - half_viewport_w
        min_camera_y = self.level_bottom + half_viewport_h
        max_camera_y = self.level_top - half_viewport_h

        self.camera_target_x = max(min(self.camera_target_x, max_camera_x), min_camera_x)
        self.camera_target_y = max(min(self.camera_target_y, max_camera_y), min_camera_y)

        # Плавное перемещение камеры к цели
        current_x, current_y = self.world_camera.position
        new_x = current_x + (self.camera_target_x - current_x) * CAMERA_LERP
        new_y = current_y + (self.camera_target_y - current_y) * CAMERA_LERP

        # Применяем ограничения к новой позиции
        new_x = max(min(new_x, max_camera_x), min_camera_x)
        new_y = max(min(new_y, max_camera_y), min_camera_y)

        self.world_camera.position = (new_x, new_y)

    def on_key_press(self, key, modifiers):
        """Обрабатывает нажатия клавиш"""
        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player.change_y = PLAYER_JUMP_SPEED
                self.player.jumping = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
            self.player.dash_direction = -1
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
            self.player.dash_direction = 1
        elif key == arcade.key.Q:
            self.activate_dash()
        elif key == arcade.key.ESCAPE:
            # Возвращаемся в меню выбора уровня
            try:
                from start_window.start_window import LevelSelectionWindow
                self.close()
                level_window = LevelSelectionWindow()
                level_window.setup()
                arcade.run()
            except ImportError:
                arcade.close_window()

    def activate_dash(self):
        """Активирует рывок в текущем направлении"""
        if self.player.dash_cooldown_timer > 0:
            return

        if self.player.change_x == 0:
            dash_x = self.player.dash_direction * DASH_SPEED
        else:
            dash_x = (1 if self.player.change_x > 0 else -1) * DASH_SPEED
            self.player.dash_direction = 1 if self.player.change_x > 0 else -1

        self.player.dashing = True
        self.player.dash_timer = DASH_DURATION
        self.player.dash_cooldown_timer = DASH_COOLDOWN

        self.player.normal_speed = abs(self.player.change_x) if self.player.change_x != 0 else PLAYER_MOVEMENT_SPEED
        self.player.change_x = dash_x

    def on_key_release(self, key, modifiers):
        """Обрабатывает отпускания клавиш"""
        if key == arcade.key.LEFT or key == arcade.key.A:
            if self.player.change_x < 0:
                self.player.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            if self.player.change_x > 0:
                self.player.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            self.player.jumping = False


def start_game(level=1):
    """Функция для запуска игры из других модулей"""
    window = GameWindow(level)
    arcade.run()


if __name__ == "__main__":
    start_game()