# cirtesub_bringup

Bringup package for the CIRTESUB platform.

This package is responsible for starting the control stack around `ros2_control`. It builds the robot description from Xacro, starts `ros2_control_node`, loads the controller configuration, and spawns the available controllers in an inactive state.

## What This Package Launches

The main launch file is [`launch/bringup.launch.py`](/home/cirtesu/cirtesub_ws/src/cirtesub_bringup/launch/bringup.launch.py).

It does the following:

1. Resolves package share paths for:
   - `cirtesub_description`
   - `thrusters_hardware_interface`
   - `cirtesub_bringup`
2. Generates `robot_description` from:
   - `cirtesub_description/urdf/cirtesub.urdf.xacro`
3. Passes the thruster lookup table path:
   - `thrusters_hardware_interface/config/t500_lookup.csv`
4. Starts `controller_manager/ros2_control_node`
5. Loads the controller configuration from:
   - [`config/ros2_control_params.yaml`](/home/cirtesu/cirtesub_ws/src/cirtesub_bringup/config/ros2_control_params.yaml)
6. Spawns these controllers as `--inactive`:
   - `thruster_test_controller`
   - `body_force_controller`
   - `body_velocity_controller`
   - `position_hold_controller`
   - `stabilize_controller`
   - `depth_hold_controller`

## Runtime Dependencies

This package depends directly on:

- `launch`
- `launch_ros`
- `ament_index_python`
- `controller_manager`
- `xacro`

At runtime it also expects these packages to be present because the launch file references them:

- `cirtesub_description`
- `thrusters_hardware_interface`
- `cirtesub_controllers`
- `forward_command_controller`

In practice, `cirtesub_bringup` is the package that ties together the robot description, hardware interface, and control plugins.

## Launch Usage

Basic usage:

```bash
ros2 launch cirtesub_bringup bringup.launch.py
```

The launch file exposes one argument:

- `environment`

Default value:

```text
sim
```

Example:

```bash
ros2 launch cirtesub_bringup bringup.launch.py environment:=real
```

This argument is forwarded to the Xacro file as:

```text
environment:=<value>
```

So the behavior of `real` vs `sim` is defined by `cirtesub_description/urdf/cirtesub.urdf.xacro`, not directly inside this package.

## Configuration Files

This package installs two configuration files:

- [`config/ros2_control_params.yaml`](/home/cirtesu/cirtesub_ws/src/cirtesub_bringup/config/ros2_control_params.yaml)
- [`config/plotjuggler_debug.xml`](/home/cirtesu/cirtesub_ws/src/cirtesub_bringup/config/plotjuggler_debug.xml)

### `ros2_control_params.yaml`

This is the main configuration file used by `ros2_control_node`.

It contains two kinds of configuration:

1. `controller_manager` configuration
2. Per-controller ROS parameters

### 1. `controller_manager` section

The top-level block:

```yaml
controller_manager:
  ros__parameters:
```

defines how `controller_manager` should start.

Important entries:

- `update_rate: 50`
  - The controller manager update loop runs at 50 Hz.
- `hardware_components_initial_state`
  - Sets `ThrustersSystem` to `inactive` on startup.
- Controller type registrations
  - This tells `controller_manager` which plugin type corresponds to each controller name.

Configured controllers:

- `thruster_test_controller`
  - Type: `forward_command_controller/ForwardCommandController`
- `body_force_controller`
  - Type: `cirtesub_controllers/BodyForceController`
- `body_velocity_controller`
  - Type: `cirtesub_controllers/BodyVelocityController`
- `position_hold_controller`
  - Type: `cirtesub_controllers/PositionHoldController`
- `stabilize_controller`
  - Type: `cirtesub_controllers/StabilizeController`
- `depth_hold_controller`
  - Type: `cirtesub_controllers/DepthHoldController`

This section does not tune controller behavior. It only declares which controllers exist and which plugin class each one uses.

### 2. Per-controller parameter blocks

Below the `controller_manager` section, each controller has its own parameter block. These parameters are read by the controller instance with the matching name.

## Controller Config Explained

### `thruster_test_controller`

Purpose:
Send effort commands directly to each thruster without allocation logic.

Configured parameters:

- `joints`
  - Explicit list of the eight thruster joints controlled by the forward command controller.
- `interface_name: effort`
  - The command interface used on each joint.

Use case:

- Hardware checks
- Direct thruster testing
- Commissioning

### `body_force_controller`

Purpose:
Convert a desired body wrench into thruster efforts.

Configured parameters:

- `input_topic: /body_force/command`
  - Topic used in topic mode to receive `geometry_msgs/msg/Wrench`.

Notes:

- This controller also supports chained mode.
- It discovers the actual thruster effort interfaces from `robot_description`, not from this YAML file.

### `body_velocity_controller`

Purpose:
Track body-frame velocity setpoints and generate a wrench request for the next stage.

Configured parameters:

- `setpoint_topic: /body_velocity_controller/setpoint`
  - Topic-mode velocity command input.
- `navigator_topic: /cirtesub/navigator/navigation`
  - State feedback source.
- `feedforward_topic: /depth_hold_controller/feedforward`
  - Output wrench topic published by this controller.
- `body_force_controller_name: body_force_controller`
  - Name of the downstream wrench-level controller whose chained interfaces may be used by name.

PID gains:

- Linear axes:
  - `kp_x`, `ki_x`, `kd_x`, `antiwindup_x`
  - `kp_y`, `ki_y`, `kd_y`, `antiwindup_y`
  - `kp_z`, `ki_z`, `kd_z`, `antiwindup_z`
- Angular axes:
  - `kp_roll`, `ki_roll`, `kd_roll`, `antiwindup_roll`
  - `kp_pitch`, `ki_pitch`, `kd_pitch`, `antiwindup_pitch`
  - `kp_yaw`, `ki_yaw`, `kd_yaw`, `antiwindup_yaw`

Important detail:

- In the current config, `feedforward_topic` points to `/depth_hold_controller/feedforward`.
- That means `body_velocity_controller` is configured to publish into `depth_hold_controller` by default rather than sending directly to `body_force_controller` as a plain topic chain.

### `position_hold_controller`

Purpose:
Hold a pose and generate body-frame velocity commands.

Configured parameters:

- `setpoint_topic: /position_hold_controller/setpoint`
  - Pose setpoint input.
- `feedforward_topic: /position_hold_controller/feedforward`
  - External feedforward velocity input.
- `navigator_topic: /cirtesub/navigator/navigation`
  - State feedback source.
- `body_velocity_controller_name: body_velocity_controller`
  - Downstream velocity controller name.
- `setpoint_frame_id: world_ned`
  - Default frame assigned to generated setpoints.

PID gains:

- `kp_*`, `ki_*`, `kd_*`, `antiwindup_*` for:
  - `x`
  - `y`
  - `z`
  - `roll`
  - `pitch`
  - `yaw`

Feedforward behavior:

- `linear_feedforward_threshold`
  - Minimum linear feedforward magnitude considered active.
- `angular_feedforward_threshold`
  - Minimum angular feedforward magnitude considered active.
- `feedforward_timeout`
  - Maximum age of a feedforward message before it is ignored.

### `stabilize_controller`

Purpose:
Stabilize roll, pitch, and yaw on top of a wrench feedforward input.

Configured parameters:

- `feedforward_topic: /stabilize_controller/feedforward`
  - Input wrench feedforward.
- `navigator_topic: /cirtesub/navigator/navigation`
  - State feedback source.
- `body_force_controller_name: body_force_controller`
  - Downstream wrench controller name.
- `enable_roll_pitch_service_name`
  - `/stabilize_controller/enable_roll_pitch`
- `disable_roll_pitch_service_name`
  - `/stabilize_controller/disable_roll_pitch`
- `allow_roll_pitch: false`
  - Startup mode for roll/pitch stabilization behavior.

Feedforward scaling:

- `feedforward_gain_x`
- `feedforward_gain_y`
- `feedforward_gain_z`
- `feedforward_gain_roll`
- `feedforward_gain_pitch`
- `feedforward_gain_yaw`

PID gains:

- `kp_roll`, `ki_roll`, `kd_roll`
- `kp_pitch`, `ki_pitch`, `kd_pitch`
- `kp_yaw`, `ki_yaw`, `kd_yaw`

Thresholds:

- `yaw_command_threshold`
- `roll_command_threshold`
- `pitch_command_threshold`

These thresholds determine when feedforward is considered active and when the controller should refresh its held setpoints from the current measured attitude.

### `depth_hold_controller`

Purpose:
Hold depth and yaw, and optionally roll/pitch, on top of a wrench feedforward input.

Configured parameters:

- `feedforward_topic: /depth_hold_controller/feedforward`
  - Input wrench feedforward.
- `navigator_topic: /cirtesub/navigator/navigation`
  - State feedback source.
- `setpoint_topic: /depth_hold_controller/set_point`
  - Published internal setpoint topic for monitoring.
- `body_force_controller_name: body_force_controller`
  - Downstream wrench controller name.
- `enable_roll_pitch_service_name`
  - `/depth_hold_controller/enable_roll_pitch`
- `disable_roll_pitch_service_name`
  - `/depth_hold_controller/disable_roll_pitch`
- `allow_roll_pitch: false`
  - Startup mode for roll/pitch stabilization behavior.

Feedforward scaling:

- `feedforward_gain_x`
- `feedforward_gain_y`
- `feedforward_gain_z`
- `feedforward_gain_roll`
- `feedforward_gain_pitch`
- `feedforward_gain_yaw`

PID gains:

- `kp_roll`, `ki_roll`, `kd_roll`
- `kp_pitch`, `ki_pitch`, `kd_pitch`
- `kp_yaw`, `ki_yaw`, `kd_yaw`
- `kp_depth`, `ki_depth`, `kd_depth`

Thresholds:

- `command_threshold`
  - Threshold used for roll, pitch, and yaw related feedforward activity.
- `depth_command_threshold`
  - Threshold used for vertical force feedforward activity.

## How the Config Fits Together

The intended stack is:

```text
Xacro/URDF
  -> robot_description
  -> ros2_control_node
  -> controller_manager
  -> controllers declared in ros2_control_params.yaml
```

At the controller level, the configuration supports several possible chains:

```text
body_force_controller
```

```text
body_velocity_controller -> body_force_controller
```

```text
body_velocity_controller -> stabilize_controller -> body_force_controller
```

```text
body_velocity_controller -> depth_hold_controller -> body_force_controller
```

```text
position_hold_controller -> body_velocity_controller -> body_force_controller
```

```text
position_hold_controller -> body_velocity_controller -> stabilize_controller -> body_force_controller
```

```text
position_hold_controller -> body_velocity_controller -> depth_hold_controller -> body_force_controller
```

The current YAML especially suggests this path:

```text
body_velocity_controller -> depth_hold_controller -> body_force_controller
```

because `body_velocity_controller.feedforward_topic` is set to `/depth_hold_controller/feedforward`.

## Inactive Startup Behavior

All controllers are spawned with `--inactive`.

That means:

- They are loaded by `controller_manager`
- They are configured
- They are not actively controlling until another node or operator activates them

This is useful because it allows the system to boot safely and lets higher-level tools decide which controller chain should be active.

## Debug Support

[`config/plotjuggler_debug.xml`](/home/cirtesu/cirtesub_ws/src/cirtesub_bringup/config/plotjuggler_debug.xml) contains a PlotJuggler layout focused on the controller topics and setpoints.

It is useful for monitoring:

- body velocity setpoints
- position hold setpoints
- stabilize setpoints
- depth hold setpoints
- feedforward topics
- navigator feedback
