#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    if (!(cin >> s)) return 0;
    int cnt[10] = {0};
    for (char c : s) {
        if (c >= '0' && c <= '9') cnt[c - '0']++;
    }
    for (int d = 9; d >= 1; --d)
        for (int i = 0; i < cnt[d]; ++i) cout << d;
    for (int i = 0; i < cnt[0]; ++i) cout << 0;
    cout << '\n';
    return 0;
}
