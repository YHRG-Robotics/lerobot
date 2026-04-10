from ..config import RobotConfig
from dataclasses import dataclass, field
from lerobot.cameras import CameraConfig
@dataclass
class SxFollowerConfig:

    # Port to connect to the arm
    port: str

    disable_torque_on_disconnect: bool = True

    max_relative_target: float | dict[str, float] | None = None

    cameras: dict[str, CameraConfig] = field(default_factory=dict)

    use_degrees: bool = True

@RobotConfig.register_subclass("so101_follower")
@RobotConfig.register_subclass("so100_follower")
@dataclass
class SxFollowerRobotConfig(RobotConfig, SxFollowerConfig):
    pass

