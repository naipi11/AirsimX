# Contributing to AirsimX / 协作开发

## 提交自己的模块

默认分支是 **`preview`**。每项改动单独建分支和 PR，目标选 `naipi11/AirsimX:preview`。不要把多个开发者的无关改动打包在一起，也不要直接推送到默认分支。

首次从自己的干净检出开始，例如开发相机时间戳：

```bash
git fetch origin
git switch -c feat/camera-timestamps origin/preview
```

只提交本模块的代码、测试和文档，然后推送工作分支，例如 `git push -u origin feat/camera-timestamps`。在 GitHub 新建 PR，说明**改了什么、为何要改、实际验证了什么**。没有仓库写权限时，从自己的 fork 提 PR，base 仍选 `naipi11/AirsimX:preview`。后续修订只需推到同一工作分支，不要重开 PR。

请另一位熟悉该模块的贡献者审阅。CI 通过且意见处理完后，有写权限的成员可以在 GitHub 上 **Squash and merge**。这是建议的团队流程；审阅和测试是否被 GitHub 强制要求取决于仓库规则，不是模板本身的功能。

## CI 检查什么？ / What does CI check?

| Check | Scope |
| --- | --- |
| `Offline (ubuntu-24.04, Python 3.12)` and `Offline (windows-2022, Python 3.12)` | SDK, tools and ROS coordinate-conversion unit tests with the pinned SDK/Gym dependencies installed. Platform-specific tests can be skipped on the other OS. |
| `Native core (Windows x64 Release)` | Restores pinned protocol inputs, verifies dependency archives, builds the native libraries and runs the AirLib tests. No Unreal installation. |
| `PR gate` | Passes only when both offline matrix legs and the native job succeed. This is the stable check name for a branch rule. |

Run the [offline suite locally](docs/airsimx/windows-development.md#run-the-offline-checks) before pushing. On the PR, open **Checks → AirsimX CI** for a failing step; when produced, JSON reports and native build/test logs are retained under the workflow run's **Artifacts** for seven days. Fix failures on the same branch. PRs targeting `preview` run automatically, as do pushes to `preview` after a merge. A maintainer can also start a manual run from **Actions**.

CI does **not** fly a vehicle, cook UE assets or run GPU training. For UE, PX4, sensors or performance changes, include a bounded simulator test or explicitly note what could not be run. See the [validation boundaries](docs/airsimx/validation.md). Keep public RPC names and `import airsim` compatible; document deliberate changes to settings, frames, units or timestamps. Do not commit credentials, local network settings, bags, binaries or assets you do not have permission to redistribute.

**For maintainers:** To enforce this workflow, use a ruleset for `preview` requiring a pull request, one approving review and the **`PR gate`** status check from GitHub Actions. Select the check after it has actually run. Adding this workflow alone does not turn on those settings.

**English quick path:** Branch from `origin/preview`, keep one module or fix per PR, push your branch (or fork), and open a PR against `naipi11/AirsimX:preview`. Request a peer review, address feedback on the same branch, then squash-merge after `PR gate` is green. Merging requires repository write access and is always subject to the repository's rules.
