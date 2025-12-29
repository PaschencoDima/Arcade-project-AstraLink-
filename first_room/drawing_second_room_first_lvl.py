import arcade
import random
import math
from arcade import SpriteList

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 675
TITLE = "Texture"

PLAYER_SCALING = 0.6
PLAYER_MOVEMENT_SPEED = 7
PLAYER_JUMP_SPEED = 17
GRAVITY = 1
PLAYER_MAX_HP = 100

DASH_SPEED = 30
DASH_DURATION = 0.3
DASH_COOLDOWN = 1.0


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

        # Начальные параметры
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

        # Изменение масштаба по X 1.02, по Y 1.005
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


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.w = width
        self.h = height

        # Инициализация физического движка
        self.physics_engine = None

        # Инициализация спрайт-листов
        self.platforms = None
        self.walls = None
        self.background_platforms = None
        self.player = None
        self.dust_particles = None  # Частицы пыли

        # Загрузка текстур
        self.texture = None
        self.wall_texture = None
        self.small_platform = None
        self.platform = None
        self.dash_get = None

        # Текстовые объекты
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

    def setup(self):
        # Загрузка текстур
        self.texture = arcade.load_texture("images/background.png")
        self.wall_texture = arcade.load_texture('images/wall.png')
        self.small_platform = arcade.load_texture('images/platform3.png')
        self.platform = arcade.load_texture('images/platform1.png')
        self.dash_get = arcade.load_texture('images/dash_get.png')

        # Инициализация спрайт-листов
        self.platforms = SpriteList()
        self.walls = SpriteList()
        self.background_platforms = arcade.SpriteList()
        self.dust_particles = arcade.SpriteList()  # Частицы пыли

        # Создание игрока
        self.player = Player()
        # Устанавливаем начальную позицию игрока НА ПОЛУ
        floor_y = 40  # Высота пола (wall_size // 2 = 40 // 2 = 20, но нужно чтобы игрок стоял на полу)
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = floor_y + self.player.height / 2  # Ставим на пол

        # Стены, потолок и пол
        wall_size = 40

        # Платформы (ОНИ СОХРАНЯЮТ КОЛЛИЗИИ!)
        platforms_data = [
            (SCREEN_WIDTH / 4 - 30, 140, self.small_platform, 2000, 800, True),  # True - есть коллизия
            (SCREEN_WIDTH / 4 * 3 + 30, 140, self.small_platform, 2000, 800, True),
            (SCREEN_WIDTH / 2 + 100, 260, self.small_platform, 2000, 800, True),
            (SCREEN_WIDTH / 2 - 100, 260, self.small_platform, 2000, 800, True),
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

        # Левая стена
        wall_y = 0
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
        wall_start_y = 0
        wall_height_available = self.h - wall_start_y
        middle_height = wall_start_y + wall_height_available // 2

        wall_y = wall_start_y
        wall_x = self.w - wall_size // 2

        while wall_y < self.h:
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

        while ceiling_x < self.w:
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

        # Пол (ВСЯ ПОВЕРХНОСТЬ ПОЛА, БЕЗ ВЫЕМКИ)
        floor_y = wall_size // 2  # Пол находится внизу экрана
        floor_x = wall_size // 2

        # Создаем пол по всей ширине экрана
        while floor_x < self.w:
            # Визуальная часть пола
            floor = arcade.Sprite()
            floor.texture = self.wall_texture
            floor.center_x = floor_x
            floor.center_y = floor_y
            floor.width = wall_size
            floor.height = wall_size
            self.walls.append(floor)

            # Коллизионная часть пола
            floor_platform = arcade.Sprite()
            floor_platform.texture = self.wall_texture
            floor_platform.center_x = floor_x
            floor_platform.center_y = floor_y
            floor_platform.width = wall_size
            floor_platform.height = wall_size
            self.platforms.append(floor_platform)
            floor_x += wall_size

        # Инициализация физического движка
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            self.platforms,
            gravity_constant=GRAVITY
        )

    def create_dust_effect(self):
        """Создаёт эффект пыли при приземлении"""
        for _ in range(random.randint(15, 20)):
            particle = DustParticle(self.player.center_x, self.player.bottom)
            self.dust_particles.append(particle)

    def on_draw(self):
        self.clear()

        # Рисуем фон
        arcade.draw_texture_rect(self.texture, arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h))

        # Рисуем стены
        self.walls.draw()

        # Рисуем платформы
        self.background_platforms.draw()

        # Рисуем объект получения рывка
        arcade.draw_texture_rect(self.dash_get, arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, 80, 80))

        # Рисуем частицы пыли
        self.dust_particles.draw()

        # Рисуем игрока
        arcade.draw_texture_rect(
            self.player.texture,
            arcade.rect.XYWH(
                self.player.center_x,
                self.player.center_y,
                self.player.width,
                self.player.height
            )
        )

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

        # Обновляем физический движок
        self.physics_engine.update()

        # Обновляем игрока
        self.player.update(delta_time)

        # Обновляем частицы пыли
        self.dust_particles.update(delta_time)

        # Проверяем, находится ли игрок на земле
        was_on_ground = self.player.on_ground
        self.player.on_ground = self.physics_engine.can_jump()

        # Обновляем текстуру игрока в зависимости от состояния
        self.player.update_texture()

        # Логика поворота лягушки (ТОЧНО КАК В ПЕРВОМ ФАЙЛЕ)
        if self.player.change_x > 0:
            # Исходная текстура лягушки смотрит влево, поэтому для движения вправо меняем scale_x
            self.player.scale_x = -PLAYER_SCALING
        elif self.player.change_x < 0:
            self.player.scale_x = PLAYER_SCALING

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

    def reset_player(self):
        """Сбрасывает позицию игрока и его состояние"""
        floor_y = 40  # Высота пола
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = floor_y + self.player.height / 2  # Ставим на пол
        self.player.change_x = 0
        self.player.change_y = 0
        self.player.hp = PLAYER_MAX_HP  # Восстанавливаем HP

        # Сбрасываем состояние рывка
        self.player.dashing = False
        self.player.dash_timer = 0
        self.player.dash_cooldown_timer = 0

        # Сбрасываем таймер неуязвимости
        self.player.invincible_timer = 0

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


def setup_game(width=1200, height=675, title="Texture"):
    game = MyGame(width, height, title)
    game.setup()
    return game


def main():
    game = setup_game()
    arcade.run()


if __name__ == "__main__":
    main()