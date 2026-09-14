#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n, q;
    if (!(cin >> n >> q)) return 0;
    vector<pair<string, string>> rules(n);
    for (int i = 0; i < n; ++i) cin >> rules[i].first >> rules[i].second;

    for (int qi = 0; qi < q; ++qi) {
        string t1, t2;
        cin >> t1 >> t2;
        int L = (int)t1.size();
        if (t2.size() != L) { cout << "0\n"; continue; }

        // 最长公共前缀 l
        int l = 0;
        while (l < L && t1[l] == t2[l]) ++l;
        // 最长公共后缀：从右往左第一个不同
        int r = L;
        while (r > l && t1[r - 1] == t2[r - 1]) --r;
        if (r < l) { cout << "0\n"; continue; }

        long long ans = 0;
        for (int i = 0; i < n; ++i) {
            int len = (int)rules[i].first.size();
            if (len == 0) continue;
            if (len < r - l) continue;               // 必须覆盖全部差异
            int lo = max(0, r - len);
            int hi = l;
            for (int pos = lo; pos <= hi; ++pos) {
                if (t1.compare(pos, len, rules[i].first) == 0 &&
                    t2.compare(pos, len, rules[i].second) == 0)
                    ++ans;
            }
        }
        cout << ans << "\n";
    }
    return 0;
}
