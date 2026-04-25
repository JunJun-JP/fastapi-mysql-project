"""Isolation Forest と AutoEncoder（Early Stopping つき）の実装。"""

import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# ── Isolation Forest ──────────────────────────────────────────────────────────

def run_isolation_forest(X: np.ndarray, contamination: float = 0.15) -> np.ndarray:
    """Returns: labels array (-1=異常, 1=正常)"""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = IsolationForest(contamination=contamination, n_estimators=100, random_state=42)
    return model.fit_predict(X_scaled)


# ── AutoEncoder ───────────────────────────────────────────────────────────────

class _AE(nn.Module):
    def __init__(self, dim: int) -> None:
        super().__init__()
        h, b = max(dim * 2, 8), max(dim // 2, 2)
        self.enc = nn.Sequential(nn.Linear(dim, h), nn.ReLU(), nn.Linear(h, b), nn.ReLU())
        self.dec = nn.Sequential(nn.Linear(b, h), nn.ReLU(), nn.Linear(h, dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dec(self.enc(x))


def run_autoencoder(
    X: np.ndarray,
    max_epochs: int = 300,
    lr: float = 1e-3,
    patience: int = 15,
    val_ratio: float = 0.2,
) -> tuple[np.ndarray, np.ndarray, float, int]:
    """
    train/test 分割 + Early Stopping でオートエンコーダーを学習する。

    Returns
    -------
    is_anomaly   : bool 配列
    errors       : 再構成誤差（全データ）
    threshold    : 平均 + 2σ
    best_epoch   : Early Stopping で決定した最適エポック数
    """
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X).astype(np.float32)
    n = len(Xs)

    # データが少なすぎる場合は分割せず固定エポックで学習
    if n < 5:
        t_all = torch.tensor(Xs)
        model = _AE(Xs.shape[1])
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = nn.MSELoss()
        model.train()
        for _ in range(50):
            loss = loss_fn(model(t_all), t_all)
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            errors = np.mean((Xs - model(t_all).numpy()) ** 2, axis=1)
        threshold = float(errors.mean() + 2 * errors.std())
        return errors > threshold, errors, threshold, 50

    # ── Train / Test 分割（固定シードで再現性を確保）────────────────────────
    rng = np.random.default_rng(42)
    idx = rng.permutation(n)
    n_val = max(1, int(n * val_ratio))
    val_idx, train_idx = idx[:n_val], idx[n_val:]

    X_train = torch.tensor(Xs[train_idx])
    X_val   = torch.tensor(Xs[val_idx])
    X_all   = torch.tensor(Xs)

    model   = _AE(Xs.shape[1])
    opt     = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    best_val_loss = float("inf")
    best_state    = None
    best_epoch    = 1
    no_improve    = 0

    # ── Early Stopping つき学習ループ ────────────────────────────────────────
    for ep in range(1, max_epochs + 1):
        # train step
        model.train()
        train_loss = loss_fn(model(X_train), X_train)
        opt.zero_grad()
        train_loss.backward()
        opt.step()

        # validation step（テストデータで誤差を確認）
        model.eval()
        with torch.no_grad():
            val_loss = loss_fn(model(X_val), X_val).item()

        if val_loss < best_val_loss - 1e-6:   # 改善した → 記録
            best_val_loss = val_loss
            best_epoch    = ep
            best_state    = {k: v.clone() for k, v in model.state_dict().items()}
            no_improve    = 0
        else:                                  # 改善しない
            no_improve += 1
            if no_improve >= patience:         # patience 回連続で改善なし → 終了
                break

    # val_loss が最も低かった時点の重みに戻す
    if best_state is not None:
        model.load_state_dict(best_state)

    # ── 全データで再構成誤差を計算 ───────────────────────────────────────────
    model.eval()
    with torch.no_grad():
        errors = np.mean((Xs - model(X_all).numpy()) ** 2, axis=1)

    threshold = float(errors.mean() + 2 * errors.std())
    return errors > threshold, errors, threshold, best_epoch
