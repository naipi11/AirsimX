# AirsimX

[English](README.md) · [安装与构建](docs/airsimx/windows-development.md) · [验证记录](docs/airsimx/validation.md) · [协作开发](CONTRIBUTING.md) · [源码预览版本](https://github.com/naipi11/AirsimX/releases)

<picture>
  <source media="(max-width: 600px)" srcset="docs/airsimx/media/ridge-flight-mobile.jpg">
  <img src="docs/airsimx/media/ridge-flight.jpg" alt="AirsimX — Unreal Engine 5 / PX4 SITL。原创封面：晨光中，一架四旋翼侧倾飞过高山。">
</picture>

**用 Unreal 显示场景，用软件里的 PX4 控制多旋翼，再用记录核对实验。** AirsimX 把 UE 5.8.4、PX4 v1.17.0 软件在环仿真（SITL）、ROS 2 Jazzy 和 Gymnasium 接到一起。沿用 AirLib 动力学、`import airsim`、RPC 名称和 Unreal 的 `AirSim` 模块，不需要为了换渲染引擎重写客户端。

这是**基于 [Microsoft AirSim](https://github.com/microsoft/AirSim) 源码独立维护的仓库**，不是微软官方续版。本次只发布源码，不附 UE 可执行程序、飞控固件或第三方场景资产。

## 从哪里开始？

| 你想做什么 | 入口 |
| --- | --- |
| 不装 UE，先确认客户端与转换逻辑能用 | [离线检查](docs/airsimx/windows-development.md#run-the-offline-checks) |
| 在 Windows 打开 Blocks | [恢复所需输入并构建编辑器](docs/airsimx/windows-development.md#build-blocks-on-windows) |
| 从 SimpleFlight 切到仿真 PX4 | [固件版本、连接顺序与配置](docs/airsimx/px4-sitl.md) |
| 用 ROS 2 看图像或用 SB3 训练 | [话题、坐标系和算法入口](docs/airsimx/experiments.md) |
| 核对规划器的航点和实际采用的地图 | [被动录制与离线判读](docs/airsimx/experiments.md#record-a-search-witness) |

克隆后，在仓库根目录用 **Windows PowerShell** 做不需要 UE 的第一项检查。首次安装 Python 依赖需要网络；测试本身不连接飞控。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r PythonClient/requirements-v01-windows.txt -r PythonClient/requirements-gym.txt
.\.venv\Scripts\python.exe -I tools/airsimx/ci/run_offline.py --output build/airsimx/ci/first
```

## 已验证到哪一步？

- **仿真平台**：在开发环境验证过 Windows / DX11 的 UE 5.8.4 Blocks 编辑器和独立 SimpleFlight 程序。这个源码预览不提供二进制下载。
- **PX4 与多机**：双机锁步和三机非锁步分别通过；另有单机连续 30 轮起降与返程。没有把单机长测当作三机长测，也没有把三机结果当作组网规模上限。
- **算法与复盘**：ROS 2 图像在 SimpleFlight 与 PX4 上都测过；图像策略的短训练是在 SimpleFlight 上。录制工具能把规划诊断与同包地图核对；离线替代地图的结果不代表某次 Blocks 飞行已经到点。

[验证范围与未验证项](docs/airsimx/validation.md)。本项目面向仿真，不提供真机部署或 HITL 验收结论。

## Star History

[![naipi11/AirsimX 的 Star 历史图](https://api.star-history.com/svg?repos=naipi11/AirsimX&type=Date)](https://www.star-history.com/#naipi11/AirsimX&Date)

[查看 GitHub 当前 Star 数](https://github.com/naipi11/AirsimX/stargazers)

## 来源与许可

感谢 Microsoft Research 的 Shital Shah 及原 AirSim 贡献者。引用研究请参考 [AirSim 原论文](https://arxiv.org/abs/1705.05065)。[作者名单](AUTHORS.md)、[MIT 许可](LICENSE)及[第三方说明](THIRD_PARTY_NOTICES.md)一并保留；引擎和外部依赖的使用条件不因仓库独立而改变。
