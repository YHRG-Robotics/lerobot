from dataclasses import dataclass

from ..config import TeleoperatorConfig


@dataclass
class SxLeaderConfig:
    """Base configuration class for SX Leader teleoperators."""

    # Port to connect to the arm
    port: str

    # Whether to use degrees for angles
    use_degrees: bool = True


@TeleoperatorConfig.register_subclass("so101_leader")
@TeleoperatorConfig.register_subclass("so100_leader")
@dataclass
class SxLeaderTeleopConfig(TeleoperatorConfig, SxLeaderConfig):
    pass


SO100LeaderConfig = SxLeaderTeleopConfig
SO101LeaderConfig = SxLeaderTeleopConfig
