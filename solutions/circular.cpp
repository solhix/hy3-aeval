// circular.cpp — 环形数组最大子段和 正确参考解
// 思路：分两种情况取 max：
//   1) 不跨首尾：普通最大子段和（Kadane）
//   2) 跨首尾：总和 - 最小子段和（去掉一段最小的子段，剩下的跨首尾）
// 注意：全负数组时跨首尾会得到空段，此时答案就是最大单元素。
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n);
    for (int i = 0; i < n; i++) cin >> a[i];

    long long total = 0;
    long long curMax = a[0], maxSum = a[0];
    long long curMin = a[0], minSum = a[0];
    total = a[0];

    for (int i = 1; i < n; i++) {
        total += a[i];
        curMax = max(a[i], curMax + a[i]);
        maxSum = max(maxSum, curMax);
        curMin = min(a[i], curMin + a[i]);
        minSum = min(minSum, curMin);
    }

    long long ans;
    if (maxSum < 0) {
        // 全负：不能取空段，答案就是最大单元素
        ans = maxSum;
    } else {
        ans = max(maxSum, total - minSum);
    }
    cout << ans << "\n";
    return 0;
}
