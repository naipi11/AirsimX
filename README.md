# AirsimX

[简体中文](README.zh-CN.md) · [Getting started](docs/airsimx/windows-development.md) · [Validation](docs/airsimx/validation.md) · [Contributing](CONTRIBUTING.md) · [Source preview releases](https://github.com/naipi11/AirsimX/releases)

<picture>
  <source media="(max-width: 600px)" srcset="docs/airsimx/media/ridge-flight-mobile.jpg">
  <img src="docs/airsimx/media/ridge-flight.jpg" alt="AirsimX — Unreal Engine 5 / PX4 SITL. Cover illustration of a quadrotor banking above alpine ridges at dawn.">
</picture>

**Run PX4 in software, fly in Unreal, and keep the evidence.** AirsimX is a multirotor simulation workbench for Unreal Engine 5.8.4. It pairs a PX4 v1.17.0 software-in-the-loop (SITL) build with an AirSim-compatible Python client, a ROS 2 Jazzy bridge, and Gymnasium environments. Existing clients still use `import airsim`; the Unreal module is still `AirSim`.

This is an independently maintained repository **derived from [Microsoft AirSim](https://github.com/microsoft/AirSim)**. It is not an official Microsoft release. This preview ships source, not a packaged simulator, autopilot firmware or third-party scene assets.

## Start with the part you need

| If you want to… | Start here |
| --- | --- |
| Check the SDK before installing Unreal | [Run the offline checks](docs/airsimx/windows-development.md#run-the-offline-checks) |
| Open the Blocks scene on Windows | [Restore the build inputs and build the editor](docs/airsimx/windows-development.md#build-blocks-on-windows) |
| Connect a simulated PX4 instead of SimpleFlight | [PX4 setup and connection order](docs/airsimx/px4-sitl.md) |
| Subscribe to images or train a policy | [ROS 2 topics and Gymnasium entry points](docs/airsimx/experiments.md) |
| Check which map a planner used | [Capture a replayable search witness](docs/airsimx/experiments.md#record-a-search-witness) |

Once a **SimpleFlight** Blocks session is running locally, this is enough to read its state. It does not arm or move a vehicle:

```python
import airsim

with airsim.MultirotorClient(port=41451, timeout_value=5) as client:
    print(client.ping())
    print(client.getMultirotorState().kinematics_estimated.position)
```

## What has been demonstrated?

On the development setup, two PX4 instances ran in lockstep, and three ran independently in free-running mode. A separate single-vehicle run completed 30 takeoff/return/landing cycles. The ROS 2 bridge delivered camera images on both SimpleFlight and PX4. These are different experiments, not one combined benchmark. [Read the results and limits](docs/airsimx/validation.md).

The source preview does **not** claim hardware-in-the-loop support, a real-aircraft deployment, certified navigation, or validated flight on every operating system. The original AirLib dynamics are retained; changing the renderer is not a measurement of physical accuracy.

## Star History

[![Star History Chart for naipi11/AirsimX](https://api.star-history.com/svg?repos=naipi11/AirsimX&type=Date)](https://www.star-history.com/#naipi11/AirsimX&Date)

[Current star count on GitHub](https://github.com/naipi11/AirsimX/stargazers)

## Credit and license

AirSim was created by Shital Shah and collaborators at Microsoft Research; the original paper is [*AirSim: High-Fidelity Visual and Physical Simulation for Autonomous Vehicles*](https://arxiv.org/abs/1705.05065). See [authors](AUTHORS.md), the [MIT license](LICENSE), and [third-party notices](THIRD_PARTY_NOTICES.md). The upstream project's history and documentation remain available at [microsoft/AirSim](https://github.com/microsoft/AirSim).
