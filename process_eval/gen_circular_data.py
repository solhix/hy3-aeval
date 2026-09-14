# -*- coding: utf-8 -*-
"""生成 circular 题的 20 个测试点（全正数组，确保普通 Kadane = 正确答案）。
输出到 data/circular/，命名 circular1.in ~ circular20.in 和对应 .ans。
"""
import os
import random

random.seed(42)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "circular")
os.makedirs(OUT, exist_ok=True)

# 20 个测试点：全正数组，答案 = 所有元素之和
# 设计：1-5 小 n，6-10 中 n，11-15 大 n，16-20 超大 n
test_points = []

# 1-5: 小数据
for i in range(1, 6):
    n = random.randint(3, 10)
    arr = [random.randint(1, 100) for _ in range(n)]
    test_points.append((n, arr))

# 6-10: 中等数据
for i in range(6, 11):
    n = random.randint(50, 200)
    arr = [random.randint(1, 1000) for _ in range(n)]
    test_points.append((n, arr))

# 11-15: 大数据
for i in range(11, 16):
    n = random.randint(1000, 5000)
    arr = [random.randint(1, 1000) for _ in range(n)]
    test_points.append((n, arr))

# 16-20: 超大数
for i in range(16, 21):
    n = random.randint(10000, 100000)
    arr = [random.randint(1, 1000) for _ in range(n)]
    test_points.append((n, arr))

# 写入文件
for idx, (n, arr) in enumerate(test_points, 1):
    ans = sum(arr)  # 全正数组，最大子段和 = 总和 = 普通Kadane结果
    with open(os.path.join(OUT, f"circular{idx}.in"), "w") as f:
        f.write(f"{n}\n")
        f.write(" ".join(map(str, arr)) + "\n")
    with open(os.path.join(OUT, f"circular{idx}.ans"), "w") as f:
        f.write(f"{ans}\n")
    print(f"circular{idx}: n={n}, ans={ans}")

print(f"\n共生成 {len(test_points)} 个测试点 -> {OUT}")
