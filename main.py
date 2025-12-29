import sys
import os


def run_start_window():
    import start_window.start_window as start_module
    start_module.main()


def run_level_selection():
    from start_window.start_window import LevelSelectionWindow
    import arcade
    window = LevelSelectionWindow()
    window.setup()
    arcade.run()


def run_story_window():
    from start_window.start_window import StoryWindow
    import arcade
    window = StoryWindow()
    window.setup()
    arcade.run()


def run_game_directly(level=1):
    import first_room.drawing_first_room_first_lvl as game_module
    game_module.start_game(level)


if __name__ == "__main__":
    # По умолчанию запускаем стартовое окно
    run_game_directly(1)

    # Другие варианты запуска:
    # run_level_selection()    # Прямо в выбор уровня
    # run_story_window()       # Прямо в историю
    # run_start_window()       # Прямо в стартовое окно