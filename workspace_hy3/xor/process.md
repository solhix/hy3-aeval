# 解题过程

## 1. 题意理解

给定长度为 $n$ 的序列 $a_1,\dots,a_n$ 和非负整数 $k$。要求选出尽可能多的**两两不相交**区间，使得每个区间的异或和都等于 $k$。求最大数量。

## 2. 算法思路

区间异或和常用**前缀异或**转化。设 $pref_0=0$，$pref_i=a_1\oplus\dots\oplus a_i$，则区间 $[l,r]$ 的异或和为 $pref_r\oplus pref_{l-1}$。要使其等于 $k$，等价于：

$$pref_r = pref_{l-1} \oplus k$$

于是问题变成：在前缀数组 $pref_0,\dots,pref_n$ 上，找尽可能多的不相交段 $[j,r]$（$j<r$），使得 $pref_r = pref_j \oplus k$。

设 $dp_i$ 表示考虑前 $i$ 个元素（即前缀 $pref_0\dots pref_i$）时最多能选多少个合法区间。转移：
- 不选以 $i$ 结尾的区间：$dp_i = dp_{i-1}$。
- 选一个以 $i$ 结尾的区间：需要找到 $j<i$ 且 $pref_j = pref_i \oplus k$，则 $dp_i = \max(dp_i, dp_j + 1)$。

为了把 $dp_j$ 快速查出来，维护数组 $best[x] = \max\{dp_j \mid pref_j = x,\ j<\text{当前}i\}$。扫描时：
- $dp_i = \max(dp_{i-1},\ best[pref_i \oplus k] + 1)$
- 更新 $best[pref_i] = \max(best[pref_i],\ dp_i)$

## 3. 复杂度分析

- **时间复杂度**：$O(n)$，每个位置只做常数次数组访问。
- **空间复杂度**：$O(2^{20})$，约 $4\,$MB，用于 $best$ 数组。$k,a_i < 2^{20}$，前缀异或值范围也在 $[0,2^{20})$ 内。

## 4. 边界处理

- $k=0$ 时转移变为 $best[pref_i]$，即找前缀异或值相同的两个位置，区间异或和为 $0$，逻辑仍然成立。
- $n=1$ 时直接判断单个元素是否等于 $k$。
- 用 $best$ 数组而非哈希表，保证 $O(1)$ 访问；初始值设为极小值，$best[0]=0$ 对应 $pref_0$。

## 5. 关键步骤

1. 读入 $n,k$ 和序列。
2. 初始化 $best[0]=0$，其余为 $-\infty$。
3. 从左到右扫描，维护当前前缀异或 $pref$ 和前一个 $dp$ 值 $dp_{prev}$。
4. 对每个位置计算 $key=pref\oplus k$，若 $best[key]$ 有效则尝试更新 $dp_i$。
5. 用 $dp_i$ 更新 $best[pref]$。
6. 输出最终的 $dp$ 值。
