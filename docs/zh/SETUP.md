# 安装与使用 SETUP

[English](../en/SETUP.md)

两条安装路径。**A 路径**最快（不装 Python，全 GUI 配置）。**B 路径**给开发者（源码运行）。

---

## A 路径 — 直接下载二进制（推荐）

### A.1. 装 VB-Audio Virtual Cable（免费，必装）

1. 下载：https://vb-audio.com/Cable/ → 点 **Download** → 解压
2. 右键 `VBCABLE_Setup_x64.exe` → **以管理员运行** → **Install Driver**
3. **重启电脑**（必须）
4. 重启后在 Windows 声音设置能看到：
   - 输出设备：`CABLE Input (VB-Audio Virtual Cable)`
   - 输入设备：`CABLE Output (VB-Audio Virtual Cable)`

如果忘了装，Doppelvoice 启动时会检测并弹出"下载 VB-Cable"按钮。

### A.2. 下载 Doppelvoice

1. 打开 [最新 release](https://github.com/TianqBu/Doppelvoice/releases/latest)
2. 下载 `Doppelvoice-vX.Y.Z-win64.zip`（约 60 MB）
3. 解压到任意有写权限的目录（`下载\`、`桌面\` 都行）

### A.3. 启动 + 配置

1. **双击 `Doppelvoice.exe`**。首次启动 7-10 秒（自解压到 `%TEMP%`），后续启动相似。
2. Settings 对话框自动弹出，填：
   - `DOUBAO_APP_KEY` = [火山引擎控制台](https://console.volcengine.com/speech/app) 里的 **App Key** 字段（不是 Access Token / API Key —— 容易混）
   - `DOUBAO_ACCESS_KEY` = 控制台里的 **Access Token** 字段
   - `DOUBAO_RESOURCE_ID` 已预填，别动
3. 点 **测试连接** 验证 → **Save**。密钥被原子写到 `%APPDATA%\Doppelvoice\.env`

完事 —— 全程不用编辑任何文件。

---

## B 路径 — 源码运行（开发者）

### B.1. 装 Python 3.10+

官网下载 https://www.python.org/downloads/ → 安装时勾选 "Add to PATH"。

```cmd
python --version
```

### B.2. 装 VB-Audio Virtual Cable —— 同 A.1

### B.3. 从源码安装 Doppelvoice

```cmd
git clone https://github.com/TianqBu/Doppelvoice.git
cd Doppelvoice
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
```

（`[dev]` extras 含 pytest + pyinstaller；只想跑不开发可省略）

### B.4. 配置密钥

复制 `.env.example` → `.env`（仓库根目录），填入：

```env
DOUBAO_APP_KEY=你的AppKey
DOUBAO_ACCESS_KEY=你的AccessToken
DOUBAO_RESOURCE_ID=volc.service_type.10053

# 可选 ────
# 9 个语言代码任选其一：zh / en / ja / id / es / pt / de / fr / zhen
# zhen = 中英互译自动模式（双向），两端都填 zhen
SOURCE_LANG=zh
TARGET_LANG=en

# 服务端降噪：0=关（默认，保留更多音色细节供克隆） / 1=开
DENOISE=0
```

### B.5. 自检

```cmd
.venv\Scripts\activate
python -m doppelvoice --check
```

预期输出：
- 列出所有音频设备（找到 `CABLE Input`）
- API 连通测试 PASS

### B.6. 启动

```cmd
python -m doppelvoice          :: 命令行模式
python -m doppelvoice --gui    :: 启动 GUI
gui.bat                        :: --gui 的便捷包装
```

---

## 在会议软件里用

### Zoom
1. 设置 → 音频 → 麦克风 → 选 `CABLE Output (VB-Audio Virtual Cable)`
   （"Output" 听上去反直觉但确实正确：它是虚拟线缆的输出端，喂给 Zoom 当麦）
2. 取消勾选 "自动调节音量"
3. 测试通话里说源语言，对方听到目标语种

### 腾讯会议 / 飞书 / Microsoft Teams / Google Meet（浏览器）
同样：音频设置 → 麦克风选 `CABLE Output`

### OBS 直播
添加"音频输入捕获"源 → 选 `CABLE Output`

---

## 推荐硬件

- 戴**有线/蓝牙耳麦**，避免麦克风采集到扬声器播放的对方声音（会形成反馈环 ——
  对方听到自己声音被翻译回来）
- 或者：扬声器和麦克风**物理上分开**（耳麦的麦 + 主扬声器）
- Windows 声音控制面板 → 麦克风属性 → 级别 = 80；**关闭** "杂音抑制" 增强
  （豆包自带降噪更强）

---

## 常见问题

**Q: "找不到 CABLE Input 设备"**
A: VB-Cable 没装好或没重启。打开 `控制面板 → 声音 → 播放` 看有没有 `CABLE Input`。
Doppelvoice 启动时也会自动检测 + 给一键下载按钮。

**Q: 会议里对方说"你的声音断断续续"**
A: GUI 里 jitter buffer 拉到 300-500 ms；或检查网络；或降低 chunk size 到 60 ms。

**Q: 延迟很高（>5 秒）**
A: 看日志 `[metrics]` 行两个指标：
- 网络延迟 > 1s：到火山机房网络慢
- 播放队列深度持续增长：消费速度跟不上，降 jitter

**Q: 想换语言对**
A: GUI 顶部下拉换源/目标语种，或 `.env` 里设 `SOURCE_LANG` / `TARGET_LANG`。
中英自动互译：**两端都填 `zhen`**。

**Q: 音色复刻听起来不像我**
A:
1. 戴宽频麦（不要用 AirPods 蓝牙 HFP），距嘴 10cm 内
2. 前 10-15s 连续自然说话让模型采样
3. 确认 `DENOISE=0`（默认；服务端降噪会磨平你的独特音色）
4. 控制台 demo 走的是不同 BFF 端点，比公开 API 强一截，公开 API 有硬天花板

**Q: 突然断流**
A: 程序会自动重连（指数退避）。频繁断通常是火山 API 配额/QPS 限制。

**Q: 对方听到自己声音的中文翻译**
A: 你在用扬声器外放，戴耳机即可。
详见 [TROUBLESHOOTING.md → 外放声学反馈环](TROUBLESHOOTING.md#外放声学反馈环)。
