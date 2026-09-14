#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    if (!(cin >> n >> m)) return 0;
    int total = n * m;
    vector<int> a(total);
    for (int i = 0; i < total; ++i) cin >> a[i];
    int score = a[0];
    int rank = 1;
    for (int i = 0; i < total; ++i)
        if (a[i] > score) ++rank;
    int c = (rank - 1) / n + 1;
    int idx = (rank - 1) % n;
    int r = (c % 2 == 1) ? (idx + 1) : (n - idx);
    cout << c << " " << r << "\n";
    return 0;
}
