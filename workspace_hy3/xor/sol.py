#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    if (!(cin >> n >> k)) return 0;
    const int MAXV = 1 << 20;
    const int NEG = -1000000000;
    vector<int> best(MAXV, NEG);
    best[0] = 0;
    int dp_prev = 0;
    int pref = 0;
    for (int i = 0; i < n; ++i) {
        int x; cin >> x;
        pref ^= x;
        int key = pref ^ k;
        int dp_i = dp_prev;
        if (best[key] != NEG) dp_i = max(dp_i, best[key] + 1);
        if (dp_i > best[pref]) best[pref] = dp_i;
        dp_prev = dp_i;
    }
    cout << dp_prev << "\n";
    return 0;
}
