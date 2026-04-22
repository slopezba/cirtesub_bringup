from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    environment = LaunchConfiguration("environment")
    use_sim = LaunchConfiguration("use_sim")
    alpha_use_fake_hardware = LaunchConfiguration("alpha_use_fake_hardware")
    alpha_left_serial_port = LaunchConfiguration("alpha_left_serial_port")
    alpha_right_serial_port = LaunchConfiguration("alpha_right_serial_port")
    alpha_left_state_update_frequency = LaunchConfiguration(
        "alpha_left_state_update_frequency"
    )
    alpha_right_state_update_frequency = LaunchConfiguration(
        "alpha_right_state_update_frequency"
    )
    initial_positions_file = LaunchConfiguration("initial_positions_file")
    alpha_desired_joint_states_topic = LaunchConfiguration(
        "alpha_desired_joint_states_topic"
    )
    alpha_joint_states_topic = LaunchConfiguration("alpha_joint_states_topic")

    description_pkg = get_package_share_directory("cirtesub_description")
    hardware_pkg = get_package_share_directory("thrusters_hardware_interface")
    bringup_pkg = get_package_share_directory("cirtesub_bringup")
    diagnostics_pkg = get_package_share_directory("sura_diagnostics")

    xacro_file = os.path.join(description_pkg, "urdf", "cirtesub_dual_alpha.urdf.xacro")
    csv_file = os.path.join(hardware_pkg, "config", "t500_lookup.csv")
    params_file = os.path.join(
        bringup_pkg, "config", "ros2_control_params_dual_alpha.yaml"
    )
    diagnostics_launch = os.path.join(
        diagnostics_pkg, "launch", "diagnostics.launch.py"
    )

    robot_description = Command(
        [
            "xacro ",
            xacro_file,
            " environment:=",
            environment,
            " lookup_csv:=",
            csv_file,
            " use_sim:=",
            use_sim,
            " alpha_use_fake_hardware:=",
            alpha_use_fake_hardware,
            " alpha_left_serial_port:=",
            alpha_left_serial_port,
            " alpha_right_serial_port:=",
            alpha_right_serial_port,
            " alpha_left_state_update_frequency:=",
            alpha_left_state_update_frequency,
            " alpha_right_state_update_frequency:=",
            alpha_right_state_update_frequency,
            " initial_positions_file:=",
            initial_positions_file,
            " alpha_desired_joint_states_topic:=",
            alpha_desired_joint_states_topic,
            " alpha_joint_states_topic:=",
            alpha_joint_states_topic,
        ]
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[params_file, {"robot_description": robot_description}],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    alpha_left_forward_velocity_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["alpha_left_forward_velocity_controller", "--inactive"],
        output="screen",
    )

    alpha_right_forward_velocity_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["alpha_right_forward_velocity_controller", "--inactive"],
        output="screen",
    )

    thruster_test_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["thruster_test_controller", "--inactive"],
        output="screen",
    )

    body_force_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["body_force_controller", "--inactive"],
        output="screen",
    )

    body_velocity_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["body_velocity_controller", "--inactive"],
        output="screen",
    )

    position_hold_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["position_hold_controller", "--inactive"],
        output="screen",
    )

    task_priority_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["task_priority_controller", "--inactive"],
        output="screen",
    )

    stabilize_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["stabilize_controller", "--inactive"],
        output="screen",
    )

    depth_hold_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["depth_hold_controller", "--inactive"],
        output="screen",
    )

    diagnostics = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(diagnostics_launch)
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "environment",
                default_value="sim",
                description="Execution environment: real or sim",
            ),
            DeclareLaunchArgument(
                "use_sim",
                default_value="true",
                description="Use the Stonefish hardware plugin for the Alpha arms.",
            ),
            DeclareLaunchArgument(
                "alpha_use_fake_hardware",
                default_value="true",
                description="Use fake Alpha hardware when not running in simulation.",
            ),
            DeclareLaunchArgument(
                "alpha_left_serial_port",
                default_value="",
                description="Serial port for the left Alpha arm in real hardware mode.",
            ),
            DeclareLaunchArgument(
                "alpha_right_serial_port",
                default_value="",
                description="Serial port for the right Alpha arm in real hardware mode.",
            ),
            DeclareLaunchArgument(
                "alpha_left_state_update_frequency",
                default_value="250",
                description="State update frequency for the left Alpha arm.",
            ),
            DeclareLaunchArgument(
                "alpha_right_state_update_frequency",
                default_value="250",
                description="State update frequency for the right Alpha arm.",
            ),
            DeclareLaunchArgument(
                "initial_positions_file",
                default_value="initial_positions.yaml",
                description="Initial positions file used by both Alpha arms.",
            ),
            DeclareLaunchArgument(
                "alpha_desired_joint_states_topic",
                default_value="/cirtesub/alpha/desired_joint_states",
                description="Topic used to send Alpha commands to Stonefish.",
            ),
            DeclareLaunchArgument(
                "alpha_joint_states_topic",
                default_value="/cirtesub/alpha/joint_states",
                description="Topic used to receive Alpha joint states from Stonefish.",
            ),
            ros2_control_node,
            diagnostics,
            joint_state_broadcaster_spawner,
            alpha_left_forward_velocity_spawner,
            alpha_right_forward_velocity_spawner,
            thruster_test_spawner,
            body_force_spawner,
            body_velocity_spawner,
            stabilize_spawner,
            depth_hold_spawner,
            position_hold_spawner,
            task_priority_spawner,
        ]
    )
