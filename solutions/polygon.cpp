#include <bits/stdc++.h>
using namespace std;
const int MOD = 998244353;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    if (!(cin >> n)) return 0;
    vector<int> a(n);
    int maxA = 0;
    for (int i = 0; i < n; ++i) {
        cin >> a[i];
        maxA = max(maxA, a[i]);
    }
    vector<int> cnt(maxA + 1, 0);
    for (int x : a) ++cnt[x];
    vector<int> pow2(n + 1, 1);
    for (int i = 1; i <= n; ++i) pow2[i] = (pow2[i - 1] * 2LL) % MOD;
    int V = maxA;
    vector<int> dp(V + 1, 0);
    dp[0] = 1;
    long long total_small = 0;
    long long ans = 0;
    for (int L = 1; L <= maxA; ++L) {
        int c = cnt[L];
        if (c > 0) {
            long long ways_all = pow2[total_small];
            long long sum_dp = 0;
            for (int s = 0; s <= L; ++s) {
                sum_dp += dp[s];
                if (sum_dp >= MOD) sum_dp -= MOD;
            }
            long long A = (ways_all - sum_dp) % MOD;
            if (A < 0) A += MOD;
            ans = (ans + 1LL * c * A) % MOD;
            if (c >= 2) {
                long long c2 = 1LL * c * (c - 1) / 2 % MOD;
                long long ways_at_least1 = (ways_all - 1 + MOD) % MOD;
                ans = (ans + c2 * ways_at_least1) % MOD;
            }
            if (c >= 3) {
                long long c_ge3 = (pow2[c] - 1 - c - (1LL * c * (c - 1) / 2 % MOD)) % MOD;
                c_ge3 = (c_ge3 % MOD + MOD) % MOD;
                ans = (ans + c_ge3 * ways_all) % MOD;
            }
        }
        for (int j = 0; j < c; ++j) {
            for (int s = V; s >= L; --s) {
                dp[s] += dp[s - L];
                if (dp[s] >= MOD) dp[s] -= MOD;
            }
        }
        total_small += c;
    }
    ans = (ans % MOD + MOD) % MOD;
    cout << ans << "\n";
    return 0;
}
