"""读写 .env 文件（保留注释和未触碰的 key）。"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from doppelvoice.config import PROJECT_ROOT


def env_path() -> Path:
    return PROJECT_ROOT / ".env"


def _dequote(value: str) -> str:
    """只剥离一对**匹配的**首尾引号，保留内部空格。

    之前的 `.strip().strip('"').strip("'")` 三连会：
      - 把不匹配的引号也吃掉（`"'weird'"` 会变 `weird`，dotenv 是 `'weird'`）
      - 内部 padding 被外层 strip 暴露后再次脱掉（`"  spaced  "` 变 `  spaced  `
        而 dotenv 给 `spaced`）
    现在严格遵守 python-dotenv 行为：只匹配成对引号，否则原样返回。
    """
    s = value.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def read_env() -> dict[str, str]:
    p = env_path()
    if not p.exists():
        return {}
    out: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = _dequote(v)
    return out


def write_env(updates: dict[str, str], *, preserve_unknown: bool = True) -> None:
    """把 updates 合并写回 .env。
    - preserve_unknown=True 时保留 .env 里我们没改的那些行（包括注释）
    """
    p = env_path()
    existing_lines: list[str] = []
    seen_keys: set[str] = set()

    if preserve_unknown and p.exists():
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                existing_lines.append(line)
                continue
            if "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k in updates:
                    # 用新值替换
                    new_val = updates[k]
                    existing_lines.append(f"{k}={new_val}")
                    seen_keys.add(k)
                else:
                    existing_lines.append(line)

    # 追加新增 key
    for k, v in updates.items():
        if k not in seen_keys:
            existing_lines.append(f"{k}={v}")

    # 原子写：先写同目录临时文件再 os.replace —— 防止崩溃中途截断密钥
    payload = "\n".join(existing_lines) + "\n"
    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix=".env.", suffix=".tmp", dir=str(p.parent)
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8-sig", newline="") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, p)
        # 尽量收紧权限（POSIX 有效；Windows 上 chmod 行为受限，不强求）
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def has_credentials() -> bool:
    """检测 .env 里是否填了 APP_KEY 和 ACCESS_KEY。"""
    env = read_env()
    return bool(env.get("DOUBAO_APP_KEY", "").strip()) and bool(
        env.get("DOUBAO_ACCESS_KEY", "").strip()
    )
