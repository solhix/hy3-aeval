#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

ll solve_one(int n, vector<array<int,3>>& a) {
    ll ans = 0;
    // 候选 0: 每人在自己最大部门，拥挤部门优先让位给人数少且等值的部门（无损失）
    vector<int> cur(n, 0), cnt(3, 0);
    ll cand0 = 0;
    for (int i = 0; i < n; ++i) {
        int bestj = 0;
        for (int j = 1; j < 3; ++j)
            if (a[i][j] > a[i][bestj] || (a[i][j] == a[i][bestj] && cnt[j] < cnt[bestj]))
                bestj = j;
        cur[i] = bestj; cand0 += a[i][bestj]; ++cnt[bestj];
    }
    bool changed = true;
    while (changed) {
        changed = false;
        for (int j = 0; j < 3; ++j) {
            if (cnt[j] <= n / 2) continue;
            for (int i = 0; i < n && cnt[j] > n / 2; ++i) {
                if (cur[i] != j) continue;
                for (int k = 0; k < 3; ++k) {
                    if (k == j) continue;
                    if (a[i][k] == a[i][j] && cnt[k] < n / 2) {
                        --cnt[j]; ++cnt[k]; cur[i] = k; changed = true; break;
                    }
                }
            }
        }
    }
    if (*max_element(cnt.begin(), cnt.end()) <= n / 2) ans = max(ans, cand0);

    // 候选 A: 恰好一个部门满 n/2
    for (int full = 0; full < 3; ++full) {
        int o1 = (full + 1) % 3, o2 = (full + 2) % 3;
        ll base_sum = 0;
        vector<ll> delta(n);
        for (int i = 0; i < n; ++i) {
            ll base = max(a[i][o1], a[i][o2]);
            base_sum += base;
            delta[i] = (ll)a[i][full] - base;
        }
        nth_element(delta.begin(), delta.begin() + n / 2, delta.end(), greater<ll>());
        ll add = 0;
        for (int i = 0; i < n / 2; ++i) add += delta[i];
        ans = max(ans, base_sum + add);
    }
    // 候选 B: 恰好两个部门满 n/2（第三空）
    for (int f1 = 0; f1 < 3; ++f1)
        for (int f2 = f1 + 1; f2 < 3; ++f2) {
            ll base_sum = 0;
            vector<ll> diff(n);
            for (int i = 0; i < n; ++i) {
                base_sum += a[i][f2];
                diff[i] = (ll)a[i][f1] - a[i][f2];
            }
            nth_element(diff.begin(), diff.begin() + n / 2, diff.end(), greater<ll>());
            ll add = 0;
            for (int i = 0; i < n / 2; ++i) add += diff[i];
            ans = max(ans, base_sum + add);
        }
    return ans;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        int n; cin >> n;
        vector<array<int,3>> a(n);
        for (int i = 0; i < n; ++i) cin >> a[i][0] >> a[i][1] >> a[i][2];
        cout << solve_one(n, a) << "\n";
    }
    return 0;
}
