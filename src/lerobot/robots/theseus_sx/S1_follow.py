import logging
import time
from functools import cached_property

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.types import RobotAction, RobotObservation
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected
from S1_SDK import S1_arm,control_mode
from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_s1_follower import SxFollowerRobotConfig

logger = logging.getLogger(__name__)
class SxFollower(Robot):
    """
    Generic SO follower base implementing common functionality for SO-100/101/10X.
    Designed to be subclassed with a per-hardware-model `config_class` and `name`.
    """

    config_class = SxFollowerRobotConfig
    name = "s1_follower"

    def __init__(self, config: SxFollowerRobotConfig):
        super().__init__(config)
        self.config = config
        # choose normalization mode depending on config if available
        self.arm = None
        try:
            print("2")
            self.arm = S1_arm(
                mode = control_mode.only_sim,
                end_effector="gripper",
            )
            print("3")
        except Exception as e:
            logger.error(f"Failed to connect to S1 arm: {e}")
            raise
        self.motors={
                "joint_1":0,
                "joint_2":1,
                "joint_3":2,
                "joint_4":3,
                "joint_5":4,
                "joint_6":5,
                "end":5,
            }
        print("init_follower2")
        self.cameras = make_cameras_from_configs(config.cameras)
        self.connect_flag = False

    @property
    def _motors_ft(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in self.motors}

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        return self.connect_flag

    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        """
        We assume that at connection time, arm is in a rest position,
        and torque can be safely disabled to run calibration.
        """

        self.arm.enable()

        for cam in self.cameras.values():
            cam.connect()

        self.configure()
        self.connect_flag = True
        logger.info(f"{self} connected.")


    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    def setup_motors(self) -> None:
        pass

    @check_if_not_connected
    def get_observation(self) -> RobotObservation:
        # Read arm position
        start = time.perf_counter()
        obs_pos = self.arm.get_pos()
        print(len(obs_pos),len(self.motors))
        obs_dict = { f"{motor}.pos": obs_pos[self.motors[motor]] for motor in self.motors}
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")

        # Capture images from cameras
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.read_latest()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    @check_if_not_connected
    def send_action(self, action: RobotAction) -> RobotAction:
        """Command arm to move to a target joint configuration.

        The relative action magnitude may be clipped depending on the configuration parameter
        `max_relative_target`. In this case, the action sent differs from original action.
        Thus, this function always returns the action actually sent.

        Raises:
            RobotDeviceNotConnectedError: if robot is not connected.

        Returns:
            RobotAction: the action sent to the motors, potentially clipped.
        """

        goal_pos = {key.removesuffix(".pos"): val for key, val in action.items() if key.endswith(".pos")}

        # Cap goal position when too far away from present position.
        # /!\ Slower fps expected due to reading from the follower.
        if self.config.max_relative_target is not None:
            present_pos = self.bus.sync_read("Present_Position")
            goal_present_pos = {key: (g_pos, present_pos[key]) for key, g_pos in goal_pos.items()}
            goal_pos = ensure_safe_goal_position(goal_present_pos, self.config.max_relative_target)

        # Send goal position to the arm
        jnt_cmd = [goal_pos[key] for key in self.motors]
        self.arm.joint_control(jnt_cmd[:6])
        # self.bus.sync_write("Goal_Position", goal_pos)
        return {f"{motor}.pos": val for motor, val in goal_pos.items()}

    @check_if_not_connected
    def disconnect(self):
        self.arm.close()
        for cam in self.cameras.values():
            cam.disconnect()

        logger.info(f"{self} disconnected.")


   
