import pygame
import random
from collections import deque
import sys
import os

# 强制设置工作目录为exe所在目录
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


# 初始化Pygame
pygame.init()
pygame.mixer.init()

# 游戏窗口设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Relaxing Match-3")

# 颜色定义
COLORS = [
    (255, 51, 153),  # 粉红
    (102, 255, 102),  # 薄荷绿
    (255, 255, 102),  # 浅黄
    (102, 178, 255),  # 天蓝
    (255, 178, 102)  # 橙黄
]

# 游戏参数
GRID_SIZE = 8
CELL_SIZE = 70
MARGIN = 5


# 获取资源文件的正确路径
def resource_path(relative_path):
    """ 获取打包后资源的绝对路径 """
    try:
        # PyInstaller创建的临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# 加载资源
try:
    # 音效设置
    pygame.mixer.music.load(resource_path('audio/background_music.mp3'))  # 需要准备音乐文件
    match_sound = pygame.mixer.Sound(resource_path('audio/match_sound.wav'))
    pygame.mixer.music.set_volume(0.3)
    match_sound.set_volume(0.6)
except Exception as e:
    print(f"音效加载失败: {e}")

# 粒子效果类
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(4, 8)
        self.life = 30
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-8, -2)
        self.gravity = 0.25

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1

    def draw(self):
        if self.life > 0:
            alpha = int(255 * (self.life / 30))
            pygame.draw.circle(screen, self.color + (alpha,),
                               (int(self.x), int(self.y)), self.radius)


# 游戏主类
class MatchThree:
    def __init__(self):
        self.grid = [[random.choice(COLORS) for _ in range(GRID_SIZE)]
                     for _ in range(GRID_SIZE)]
        self.score = 0
        self.combo = 0
        self.last_match_time = 0
        self.particles = []
        self.font = pygame.font.Font(None, 36)
        self.combo_font = pygame.font.Font(None, 48)

        # 启动背景音乐
        pygame.mixer.music.play(-1)

    def find_matches(self, x, y):
        # 使用BFS算法查找相邻同色块
        target_color = self.grid[y][x]
        visited = set()
        queue = deque()
        matches = []

        queue.append((x, y))
        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) not in visited:
                visited.add((cx, cy))
                matches.append((cx, cy))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if self.grid[ny][nx] == target_color:
                            queue.append((nx, ny))
        return matches if len(matches) >= 2 else []

    def create_particles(self, x, y):
        # 创建粒子爆炸效果
        base_x = x * (CELL_SIZE + MARGIN) + CELL_SIZE // 2
        base_y = y * (CELL_SIZE + MARGIN) + CELL_SIZE // 2
        for _ in range(20):
            self.particles.append(Particle(base_x, base_y, self.grid[y][x]))

    def update_grid(self, matches):
        # 处理方块消除和下落
        for x, y in matches:
            self.create_particles(x, y)
            self.grid[y][x] = None

        # 处理方块下落
        for x in range(GRID_SIZE):
            column = [self.grid[y][x] for y in range(GRID_SIZE) if self.grid[y][x] is not None]
            column = column + [random.choice(COLORS) for _ in range(GRID_SIZE - len(column))]
            for y in range(GRID_SIZE):
                self.grid[y][x] = column[y]

    def draw(self):
        screen.fill((245, 245, 245))  # 浅灰色背景

        # 绘制网格方块
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(
                    x * (CELL_SIZE + MARGIN) + MARGIN,
                    y * (CELL_SIZE + MARGIN) + MARGIN,
                    CELL_SIZE, CELL_SIZE
                )
                if self.grid[y][x]:
                    pygame.draw.rect(screen, self.grid[y][x], rect)
                    pygame.draw.rect(screen, (255, 255, 255), rect, 2)

        # 绘制粒子效果
        for p in self.particles[:]:
            p.update()
            p.draw()
            if p.life <= 0:
                self.particles.remove(p)

        # 绘制分数和连击
        score_text = self.font.render(f"Score: {self.score}", True, (50, 50, 50))
        screen.blit(score_text, (10, 10))

        if self.combo > 1:
            combo_text = self.combo_font.render(
                f"Combo x{self.combo}!", True,
                (255, 51, 153) if self.combo > 3 else (102, 178, 255)
            )
            screen.blit(combo_text, (SCREEN_WIDTH - 200, 10))

    def handle_click(self, pos):
        x, y = pos
        grid_x = (x - MARGIN) // (CELL_SIZE + MARGIN)
        grid_y = (y - MARGIN) // (CELL_SIZE + MARGIN)

        if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
            matches = self.find_matches(grid_x, grid_y)
            if matches:
                current_time = pygame.time.get_ticks()
                # 连击计算（1.5秒内连续消除）
                if current_time - self.last_match_time < 1500:
                    self.combo += 1
                else:
                    self.combo = 1

                self.score += len(matches) * 10 * self.combo
                self.last_match_time = current_time
                self.update_grid(matches)
                match_sound.play()


# 游戏初始化
game = MatchThree()
clock = pygame.time.Clock()
running = True

# 游戏主循环
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            game.handle_click(pygame.mouse.get_pos())

    game.draw()
    pygame.display.flip()
    clock.tick(30)

pygame.quit()