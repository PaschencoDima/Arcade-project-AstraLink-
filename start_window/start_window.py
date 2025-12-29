import arcade
import sys
import os
import time

# Добавляем путь к корневой папке проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
TITLE = "Game Menu"


def get_resource_path(filename):
    """Получает правильный путь к ресурсу"""
    # Проверяем разные возможные места расположения файлов
    possible_paths = [
        filename,  # Относительный путь
        os.path.join("start_window", filename),  # В папке start_window
        os.path.join("images", filename),  # В корневой папке images
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Если файл не найден, возвращаем оригинальный путь
    return filename


class StoryWindow(arcade.Window):
    """Окно с историей, которая появляется постепенно"""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "История")
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT

        # Текст истории
        self.story_lines = [
            'Лог загрузки.',
            'Идентификатор пользователя: [УДАЛЕНО]',
            'Загрузка агента...',
            'Агент: неизвестный санитар.',
            'Цель: диагностика и очистка.',
            'Система: AstraLink v.7.4.2 "Гелиос".',
            'Статус: аварийное завершение работы, 712 циклов назад.',
            'Запуск...',
        ]

        # Текущие отображаемые символы
        self.displayed_text = []
        self.current_line = 0
        self.char_index = 0
        self.last_update_time = 0
        self.char_delay = 0.05  # Задержка между символами

        # Флаг завершения анимации
        self.animation_complete = False

        self.setup()

    def setup(self):
        self.texture = arcade.load_texture(get_resource_path('images/background.png'))

    def on_draw(self):
        self.clear()

        # Рисуем фон
        arcade.draw_rect_filled(
            arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h),
            arcade.color.BLACK
        )

        # Рисуем текущий текст
        y_position = self.h - 200
        for i, line in enumerate(self.displayed_text):
            if i == self.current_line:
                # Текущая строка с анимацией
                color = arcade.color.RED
            else:
                # Уже отображенные строки
                color = arcade.color.DARK_RED

            text = arcade.Text(
                line,
                self.w // 2,
                y_position,
                color,
                24,
                font_name='segoe print',
                align="center",
                anchor_x="center",
                width=self.w - 100
            )
            text.draw()
            y_position -= 40

        # Инструкция для продолжения
        if self.animation_complete:
            instruction = arcade.Text(
                "Нажмите любую клавишу для продолжения...",
                self.w // 2,
                100,
                arcade.color.DARK_RED,
                20,
                font_name='playbill',
                align="center",
                anchor_x="center"
            )
            instruction.draw()

    def on_update(self, delta_time):
        # Обновляем анимацию текста
        self.last_update_time += delta_time

        if not self.animation_complete and self.last_update_time >= self.char_delay:
            self.last_update_time = 0

            # Если еще есть символы в текущей строке
            if self.char_index < len(self.story_lines[self.current_line]):
                # Добавляем следующий символ
                if len(self.displayed_text) <= self.current_line:
                    self.displayed_text.append("")

                self.displayed_text[self.current_line] += self.story_lines[self.current_line][self.char_index]
                self.char_index += 1
            else:
                # Переходим к следующей строке
                self.current_line += 1
                self.char_index = 0

                # Если все строки отображены
                if self.current_line >= len(self.story_lines):
                    self.animation_complete = True

    def on_key_press(self, key, modifiers):
        # Пропускаем анимацию при нажатии любой клавиши
        if not self.animation_complete:
            # Показываем весь текст сразу
            self.displayed_text = self.story_lines[:]
            self.animation_complete = True
        else:
            # Переходим к выбору уровня
            self.close()
            from start_window.start_window import LevelSelectionWindow
            level_window = LevelSelectionWindow()
            level_window.setup()
            arcade.run()


class LevelSelectionWindow(arcade.Window):
    """Окно выбора уровня"""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Выбор уровня")
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT

        # Уровни (сначала доступен только 1)
        self.levels = [
            {"number": 1, "name": "Начальный уровень", "available": True, "completed": False},
            {"number": 2, "name": "Средний уровень", "available": False, "completed": False},
            {"number": 3, "name": "Сложный уровень", "available": False, "completed": False}
        ]

        # Размеры кнопок уровня
        self.level_button_width = 300
        self.level_button_height = 100
        self.level_button_spacing = 50

        # Кнопка возврата
        self.back_button_width = 200
        self.back_button_height = 60

        self.setup()

    def setup(self):
        # Загружаем текстуры
        self.texture = arcade.load_texture(get_resource_path("images/background.png"))
        self.button_texture = arcade.load_texture(get_resource_path('images/button.png'))

        # Создаем текстовые объекты для кнопок
        self.level_texts = []
        for level in self.levels:
            if level["available"]:
                color = arcade.color.WHITE
            else:
                color = arcade.color.GRAY

            level_text = arcade.Text(
                f"",
                0, 0,
                color,
                20,
                align="center",
                anchor_x="center",
                anchor_y="center",
                multiline=True,
                width=self.level_button_width - 20
            )

            # Добавляем иконку замка для недоступных уровней
            if not level["available"]:
                level_text.text += "\n🔒"

            self.level_texts.append(level_text)

    def on_draw(self):
        self.clear()

        # Рисуем фон
        arcade.draw_texture_rect(
            self.texture,
            arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h)
        )

        # Рассчитываем начальную позицию для кнопок уровней
        total_height = len(self.levels) * self.level_button_height + (len(self.levels) - 1) * self.level_button_spacing
        start_y = self.h // 2 + total_height // 2 - self.level_button_height // 2

        # Рисуем кнопки уровней
        for i, level in enumerate(self.levels):
            button_x = self.w // 2
            button_y = start_y - i * (self.level_button_height + self.level_button_spacing)

            # Рисуем кнопку
            if level["available"]:
                alpha = 255
            else:
                alpha = 128  # Полупрозрачный для недоступных

            arcade.draw_texture_rect(
                self.button_texture,
                arcade.rect.XYWH(
                    button_x,
                    button_y,
                    self.level_button_width,
                    self.level_button_height
                ),
                alpha=alpha
            )

            # Обновляем позицию текста и рисуем его
            self.level_texts[i].x = button_x
            self.level_texts[i].y = button_y
            self.level_texts[i].draw()

            # Отображаем звезды за пройденные уровни
            if level["completed"]:
                stars_text = arcade.Text(
                    "⭐" * 3,  # 3 звезды за пройденный уровень
                    button_x + self.level_button_width // 2 - 30,
                    button_y - self.level_button_height // 2 + 15,
                    arcade.color.YELLOW,
                    20
                )
                stars_text.draw()

        # Кнопка возврата
        back_x = self.w // 2
        back_y = 100

        arcade.draw_texture_rect(
            self.button_texture,
            arcade.rect.XYWH(
                back_x,
                back_y,
                self.back_button_width,
                self.back_button_height
            )
        )

    def on_mouse_press(self, x, y, button, modifiers):
        # Проверяем клики по кнопкам уровней
        total_height = len(self.levels) * self.level_button_height + (len(self.levels) - 1) * self.level_button_spacing
        start_y = self.h // 2 + total_height // 2 - self.level_button_height // 2

        for i, level in enumerate(self.levels):
            if not level["available"]:
                continue  # Пропускаем недоступные уровни

            button_x = self.w // 2
            button_y = start_y - i * (self.level_button_height + self.level_button_spacing)

            button_left = button_x - self.level_button_width // 2
            button_right = button_x + self.level_button_width // 2
            button_bottom = button_y - self.level_button_height // 2
            button_top = button_y + self.level_button_height // 2

            if (button_left <= x <= button_right and
                    button_bottom <= y <= button_top):

                # Запускаем игру с выбранным уровнем
                self.close()
                from first_room.drawing_first_room_first_lvl import start_game
                start_game(level["number"])
                return

        # Проверяем клик по кнопке возврата
        back_x = self.w // 2
        back_y = 100

        back_left = back_x - self.back_button_width // 2
        back_right = back_x + self.back_button_width // 2
        back_bottom = back_y - self.back_button_height // 2
        back_top = back_y + self.back_button_height // 2

        if (back_left <= x <= back_right and
                back_bottom <= y <= back_top):

            # Возвращаемся к окну истории
            self.close()
            story_window = StoryWindow()
            story_window.setup()
            arcade.run()

    def on_key_press(self, key, modifiers):
        # Быстрый выбор уровня клавишами 1, 2, 3
        if key == arcade.key.KEY_1 or key == arcade.key.NUM_1:
            if self.levels[0]["available"]:
                self.close()
                from first_room.drawing_first_room_first_lvl import start_game
                start_game(1)
        elif key == arcade.key.KEY_2 or key == arcade.key.NUM_2:
            if len(self.levels) > 1 and self.levels[1]["available"]:
                self.close()
                from first_room.drawing_first_room_first_lvl import start_game
                start_game(2)
        elif key == arcade.key.KEY_3 or key == arcade.key.NUM_3:
            if len(self.levels) > 2 and self.levels[2]["available"]:
                self.close()
                from first_room.drawing_first_room_first_lvl import start_game
                start_game(3)
        elif key == arcade.key.ESCAPE:
            # Возвращаемся к истории
            self.close()
            story_window = StoryWindow()
            story_window.setup()
            arcade.run()


class StartWindow(arcade.Window):
    """Начальное окно с кнопкой"""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT
        self.button_clicked = False

        # Размеры кнопки
        self.button_width = 600
        self.button_height = 240

        # Позиция кнопки по центру экрана
        self.button_x = self.w // 2
        self.button_y = self.h // 2

        self.setup()

    def setup(self):
        # Загружаем текстуры
        self.texture = arcade.load_texture(get_resource_path("images/background.png"))
        self.button_texture = arcade.load_texture(get_resource_path('images/button.png'))

    def on_draw(self):
        self.clear()

        # Рисуем фон
        arcade.draw_texture_rect(
            self.texture,
            arcade.rect.XYWH(self.w // 2, self.h // 2, self.w, self.h)
        )

        # Рисуем кнопку по центру
        arcade.draw_texture_rect(
            self.button_texture,
            arcade.rect.XYWH(
                self.button_x,
                self.button_y,
                self.button_width,
                self.button_height
            )
        )

    def on_mouse_press(self, x, y, button, modifiers):
        # Проверяем, попал ли клик по кнопке
        button_left = self.button_x - self.button_width // 2
        button_right = self.button_x + self.button_width // 2
        button_bottom = self.button_y - self.button_height // 2
        button_top = self.button_y + self.button_height // 2

        if (button_left <= x <= button_right and
                button_bottom <= y <= button_top):
            self.button_clicked = True

            # Закрываем стартовое окно и открываем историю
            self.close()
            story_window = StoryWindow()
            story_window.setup()
            arcade.run()

    def on_key_press(self, key, modifiers):
        # Любая клавиша также запускает историю
        self.close()
        story_window = StoryWindow()
        story_window.setup()
        arcade.run()

    def on_mouse_release(self, x, y, button, modifiers):
        self.button_clicked = False


def main():
    window = StartWindow()
    arcade.run()


if __name__ == "__main__":
    main()