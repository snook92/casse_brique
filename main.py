import asyncio
import pygame
from game import Game


async def main():
    game = Game()
    while True:
        game.run_frame()
        await asyncio.sleep(0)


asyncio.run(main())
