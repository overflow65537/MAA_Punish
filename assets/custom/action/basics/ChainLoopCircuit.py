# Copyright (c) 2024-2025 MAA_Punish
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
MAA_Punish
MAA_Punish 链合回路求解器
作者:overflow65537
"""

from maa.context import Context
from maa.custom_action import CustomAction
import json
import random
import time

from numpy import gradient


class ChainLoopCircuit(CustomAction):
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        image = context.tasker.controller.post_screencap().wait().get()
        S4_ball = context.run_recognition("识别闪星_链合回路", image)
        if S4_ball and S4_ball.best_result:
            x, y = (
                S4_ball.best_result.box[0] + S4_ball.best_result.box[2] // 2,
                S4_ball.best_result.box[1] + S4_ball.best_result.box[3] // 2,
            )
            context.tasker.controller.post_click(x, y)
            time.sleep(0.1)
            context.tasker.controller.post_click(x, y)
            return CustomAction.RunResult(success=True)

        S2_ball = context.run_recognition("识别爆破_链合回路", image)
        if S2_ball and S2_ball.best_result:
            x, y = (
                S2_ball.best_result.box[0] + S2_ball.best_result.box[2] // 2,
                S2_ball.best_result.box[1] + S2_ball.best_result.box[3] // 2,
            )
            context.tasker.controller.post_click(x, y)
            time.sleep(0.1)
            context.tasker.controller.post_click(x, y)
            return CustomAction.RunResult(success=True)

        S3_ball = context.run_recognition("识别纵斩_链合回路", image)
        if S3_ball and S3_ball.best_result:
            x, y = (
                S3_ball.best_result.box[0] + S3_ball.best_result.box[2] // 2,
                S3_ball.best_result.box[1] + S3_ball.best_result.box[3] // 2,
            )
            context.tasker.controller.post_click(x, y)
            time.sleep(0.1)
            context.tasker.controller.post_click(x, y)
            return CustomAction.RunResult(success=True)
        S1_ball = context.run_recognition("识别快枪_链合回路", image)
        if S1_ball and S1_ball.best_result:
            x, y = (
                S1_ball.best_result.box[0] + S1_ball.best_result.box[2] // 2,
                S1_ball.best_result.box[1] + S1_ball.best_result.box[3] // 2,
            )
            context.tasker.controller.post_click(x, y)
            time.sleep(0.1)
            context.tasker.controller.post_click(x, y)
            return CustomAction.RunResult(success=True)

        bul_ball = context.run_recognition("识别蓝球_链合回路", image)
        red_ball = context.run_recognition("识别红球_链合回路", image)
        yel_ball = context.run_recognition("识别黄球_链合回路", image)
        gra_ball = context.run_recognition("识别灰球_链合回路", image)

        S1_ball = context.run_recognition("识别快枪_链合回路", image)
        S2_ball = context.run_recognition("识别爆破_链合回路", image)
        S3_ball = context.run_recognition("识别纵斩_链合回路", image)

        matrix = [[0] * 8 for _ in range(8)]
        reco_list = [
            bul_ball,
            red_ball,
            yel_ball,
            gra_ball,
            S1_ball,
            S2_ball,
            S3_ball,
            S4_ball,
        ]
        for idx, recognition_data in enumerate(reco_list):
            matrix = self.parse_puzzle_layout(
                recognition_data, matrix, fill_value=idx + 1
            )
        for i in matrix:
            print(i)
        result = self.find_max_elimination(matrix)
        if result:
            (start_i, start_j), (end_i, end_j), count = result
            print(
                f"最佳移动: 从({start_i}, {start_j})移动到({end_i}, {end_j})，可消除{count}个球"
            )
            begin_x, begin_y = self.get_click_position(start_i, start_j)
            end_x, end_y = self.get_click_position(end_i, end_j)
            context.tasker.controller.post_swipe(
                begin_x, begin_y, end_x, end_y, 1000
            ).wait()
        else:
            print("没有找到有效移动")
        return CustomAction.RunResult(success=True)

    def parse_puzzle_layout(self, recognition_data, matrix, fill_value=-1):
        """解析拼图板布局
        Args:
            recognition_data: 识别数据
            fill_value: 用于填充识别到位置的数值，默认为-1
            matrix: 外部传入的8x8矩阵，如果为None则新建
        Returns:
            8x8的二维数组，识别到的位置用fill_value填充
        """
        if not recognition_data:
            return matrix

        # 计算每个单元格的Y坐标(行)和X坐标(列)
        cell_height = 632 // 8
        cell_width = 627 // 8

        ROW_Y = [61 + i * cell_height + cell_height // 2 for i in range(8)]
        COL_X = [430 + j * cell_width + cell_width // 2 for j in range(8)]

        for item in recognition_data.filterd_results:
            x, y, w, h = item.box

            # 行列索引查找逻辑
            row_idx = next(
                (
                    i
                    for i, ry in enumerate(ROW_Y)
                    if ry - cell_height // 2 <= y <= ry + cell_height // 2
                ),
                None,
            )
            col_idx = next(
                (
                    i
                    for i, cx in enumerate(COL_X)
                    if cx - cell_width // 2 <= x <= cx + cell_width // 2
                ),
                None,
            )

            if row_idx is not None and col_idx is not None:
                matrix[row_idx][col_idx] = fill_value

        return matrix

    def find_max_elimination(self, board):
        """找出能消除最多球的方案，比较技能球和普通消球的收益
        Args:
            board: 8x8游戏板
        Returns:
            (最佳移动的起始位置, 目标位置, 消除数量), 如果没有有效移动则返回None
        """
        max_eliminated = 0
        best_move = None
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 上下左右四个方向

        # 技能球移动分数
        skill_moves = []
        for i in range(8):
            for j in range(8):
                if board[i][j] in [5, 6, 7, 8]:  # 是技能球
                    for dx, dy in directions:
                        ni, nj = i + dx, j + dy
                        if (
                            0 <= ni < 8 and 0 <= nj < 8 and board[ni][nj] != 0
                        ):  # 0值检查
                            eliminated = self.count_skill_eliminations(board[i][j])
                            skill_moves.append(((i, j), (ni, nj), eliminated))

        # 普通消球分数
        normal_move = None
        normal_eliminated = 0
        for i in range(8):
            for j in range(8):
                if board[i][j] == 0:  # 0值位置
                    continue
                for dx, dy in directions:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 8 and 0 <= nj < 8 and board[ni][nj] != 0:  # 0值检查
                        temp_board = [row[:] for row in board]
                        temp_board[i][j], temp_board[ni][nj] = (
                            temp_board[ni][nj],
                            temp_board[i][j],
                        )
                        eliminated = self.count_eliminations(temp_board)
                        if eliminated > normal_eliminated:
                            normal_eliminated = eliminated
                            normal_move = ((i, j), (ni, nj), normal_eliminated)

        # 比较技能球和普通消球的收益
        best_skill_move = max(skill_moves, key=lambda x: x[2], default=None)
        if best_skill_move and (
            not normal_move or best_skill_move[2] >= normal_eliminated
        ):
            return best_skill_move
        elif normal_move:
            return normal_move

        return None

    def count_skill_eliminations(self, skill_type):
        """计算技能球的消除数量
        Args:
            skill_type: 技能球类型(5-8)
        Returns:
            能消除的球数
        """
        if skill_type == 5:  # 快枪 - 随机4个
            return 4
        elif skill_type == 6:  # 爆破 - 3x3区域(8个)
            return 8
        elif skill_type == 7:  # 纵斩 - 整列(8个)
            return 8
        elif skill_type == 8:  # 闪星 - 随机12个
            return 12
        return 0

    def count_eliminations(self, board):
        """计算当前板子能消除的球数
        Args:
            board: 8x8游戏板
        Returns:
            能消除的球数
        """
        to_remove = set()

        # 查找水平匹配
        for i in range(8):
            for j in range(6):
                if (
                    board[i][j] > 0
                    and board[i][j] == board[i][j + 1] == board[i][j + 2]
                ):
                    to_remove.update({(i, j), (i, j + 1), (i, j + 2)})
                    # 检查更长的匹配
                    k = j + 3
                    while k < 8 and board[i][k] == board[i][j]:
                        to_remove.add((i, k))
                        k += 1

        # 查找垂直匹配
        for j in range(8):
            for i in range(6):
                if (
                    board[i][j] > 0
                    and board[i][j] == board[i + 1][j] == board[i + 2][j]
                ):
                    to_remove.update({(i, j), (i + 1, j), (i + 2, j)})
                    # 检查更长的匹配
                    k = i + 3
                    while k < 8 and board[k][j] == board[i][j]:
                        to_remove.add((k, j))
                        k += 1

        # 处理技能球
        for i, j in list(to_remove):
            val = board[i][j]
            if val in [5, 6, 7, 8]:  # 技能球
                if val == 5:  # 随机消除4个球
                    to_remove.update(
                        {(random.randint(0, 7), random.randint(0, 7)) for _ in range(4)}
                    )
                elif val == 6:  # 3x3区域(9个格子)
                    to_remove.update(
                        {
                            (i + dx, j + dy)
                            for dx in [-1, 0, 1]
                            for dy in [-1, 0, 1]
                            if 0 <= i + dx < 8 and 0 <= j + dy < 8
                        }
                    )
                elif val == 7:  # 整列(8个格子)
                    to_remove.update({(x, j) for x in range(8)})
                elif val == 8:  # 随机消除12个球
                    to_remove.update(
                        {
                            (random.randint(0, 7), random.randint(0, 7))
                            for _ in range(12)
                        }
                    )

        return len(to_remove)

    def get_click_position(self, row, col):
        """将二维数组位置转换为屏幕点击坐标
        Args:
            row: 行索引(0-7)
            col: 列索引(0-7)
        Returns:
            (x, y) 屏幕坐标
        """
        # 棋盘ROI参数
        board_x, board_y, board_width, board_height = 430, 61, 627, 632

        # 计算单元格尺寸
        cell_width = board_width // 8
        cell_height = board_height // 8

        # 计算中心点坐标
        x = board_x + col * cell_width + cell_width // 2
        y = board_y + row * cell_height + cell_height // 2

        return (x, y)
