"""游戏入口 —— 初始化 pygame 并启动游戏引擎主循环。"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pygame
from src.core.engine import Engine
from src.scenes.menu_scene import MenuScene
from src.graphics.sprite_atlas import init_sprites
from src.audio.sound_manager import SoundManager


def main():
    """初始化 pygame、加载精灵、创建引擎并进入主菜单。"""
    pygame.init()
    pygame.key.set_repeat(200, 50)  # 启用按键重复，支持门谜题和 UI 持续输入
    init_sprites()                  # 生成所有程序化精灵并加载自定义 PNG
    sound_manager = SoundManager(master_volume=0.7)
    engine = Engine()               # 创建游戏引擎实例
    engine.state_machine.push(MenuScene(engine, sound_manager))  # 推入主菜单场景
    engine.run()                    # 进入事件/渲染主循环
    pygame.quit()                   # 退出 pygame


if __name__ == "__main__":
    main()
