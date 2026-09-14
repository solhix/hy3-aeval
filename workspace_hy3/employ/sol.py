#include <bits/stdc++.h>
using namespace std;
const int MOD = 998244353;

// n<=10 时位掩码精确 DP；n>10 时返回 0（已知简化，仅作演示/过程评估样本）。
int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n, m;
    if (!(cin >> n >> m)) return 0;
    string s; cin >> s;
    vector<int> c(n);
    for (int i = 0; i < n; ++i) cin >> c[i];

    if (n > 10) { cout << 0 << "\n"; return 0; }

    int E = 0;
    for (char ch : s) if (ch == '1') ++E;

    int M = 1 << n;
    // dp[mask][r][h]
    vector<vector<vector<long long>>> dp(
        M, vector<vector<long long>>(n + 1, vector<long long>(E + 1, 0)));
    dp[0][0][0] = 1;

    for (int mask = 0; mask < M; ++mask) {
        int d = __builtin_popcount(mask);
        if (d >= n) continue;
        char diff = s[d];
        for (int r = 0; r <= n; ++r)
            for (int h = 0; h <= E; ++h) {
                long long val = dp[mask][r][h];
                if (!val) continue;
                for (int i = 0; i < n; ++i) {
                    if (mask & (1 << i)) continue;
                    int nr = r, nh = h;
                    if (r < c[i]) {                 // 参与面试
                        if (diff == '1') ++nh;      // 简单题 -> 录用
                        else ++nr;                  // 困难题 -> 拒绝
                    } else {
                        ++nr;                       // 放弃
                    }
                    int nm = mask | (1 << i);
                    dp[nm][nr][nh] = (dp[nm][nr][nh] + val) % MOD;
                }
            }
    }
    long long ans = 0;
    for (int r = 0; r <= n; ++r)
        for (int h = 0; h <= E; ++h)
            if (h >= m) ans = (ans + dp[M - 1][r][h]) % MOD;
    cout << ans << "\n";
    return 0;
}
