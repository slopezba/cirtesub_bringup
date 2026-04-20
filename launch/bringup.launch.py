from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    environment = LaunchConfiguration("environment")

    description_pkg = get_package_share_directory("cirtesub_description")
    hardware_pkg = get_package_share_directory("thrusters_hardware_interface")
    bringup_pkg = get_package_share_directory("cirtesub_bringup")
    diagnostics_pkg = get_package_share_directory("sura_diagnostics")

    xacro_file = os.path.join(description_pkg, "urdf", "cirtesub.urdf.xacro")
    csv_file = os.path.join(hardware_pkg, "config", "t500_lookup.csv")
    params_file = os.path.join(bringup_pkg, "config", "ros2_control_params.yaml")
    diagnostics_launch = os.path.join(diagnostics_pkg, "launch", "diagnostics.launch.py")

    robot_description = Command([
        "xacro ",
        xacro_file,
        " environment:=", environment,
        " lookup_csv:=", csv_file
    ])

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            params_file,
            {"robot_description": robot_description}
        ],
        output="screen"
    )

    thruster_test_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["thruster_test_controller", "--inactive"],
        output="screen"
    )

    body_force_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["body_force_controller", "--inactive"],
        output="screen"
    )

    body_velocity_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["body_velocity_controller", "--inactive"],
        output="screen"
    )

    position_hold_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["position_hold_controller", "--inactive"],
        output="screen"
    )

    stabilize_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["stabilize_controller", "--inactive"],
        output="screen"
    )

    depth_hold_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["depth_hold_controller", "--inactive"],
        output="screen"
    )

    diagnostics = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(diagnostics_launch)
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "environment",
            default_value="sim",
            description="Execution environment: real or sim"
        ),
        ros2_control_node,
        diagnostics,
        thruster_test_spawner,
        body_force_spawner,
        body_velocity_spawner,
        stabilize_spawner,
        depth_hold_spawner,
        position_hold_spawner,
    ])
