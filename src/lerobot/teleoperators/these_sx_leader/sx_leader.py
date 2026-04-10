# !/usr/bin/env python

# Copyright 2026 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import time

# from lerobot.motors import Motor, MotorCalibration, MotorNormMode
# from lerobot.motors.feetech import (
#     FeetechMotorsBus,
#     OperatingMode,
# )
from lerobot.utils.decorators import check_if_already_connected, check_if_not_connected
from S1_SDK import S1_arm,control_mode
from ..teleoperator import Teleoperator
from .config_sx_leader import SxLeaderTeleopConfig

logger = logging.getLogger(__name__)


class SxLeader(Teleoperator):
    """Generic SO leader base for SO-100/101/10X teleoperators."""

    config_class = SxLeaderTeleopConfig
    name = "sx_leader"

    def __init__(self, config: SxLeaderTeleopConfig):
        super().__init__(config)
        self.config = config
        self.arm = None
        self.motors={
            "joint_1": 0,
            "joint_2": 1,
            "joint_3": 2,
            "joint_4": 3,
            "joint_5": 4,
            "joint_6": 5,
            "teach": 6,
        }
        try:
            self.arm = S1_arm(
                dev = self.config.port,
                mode = control_mode.only_sim
            )
        except:
            logger.error("Failed to initialize arm")


    @property
    def action_features(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in self.motors}

    @property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def is_connected(self) -> bool:
        return self.arm is not None

    @check_if_already_connected
    def connect(self, calibrate: bool = True) -> None:
        self.arm.enable()

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
    def get_action(self) -> dict[str, float]:
        start = time.perf_counter()
        action = self.arm.get_pos()
        self.arm.gravity()
        action = { f"{motor}.pos": action[self.motors[motor]] for motor in self.motors}
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read action: {dt_ms:.1f}ms")
        return action

    def send_feedback(self, feedback: dict[str, float]) -> None:
        # TODO: Implement force feedback
        raise NotImplementedError

    @check_if_not_connected
    def disconnect(self) -> None:
        self.arm.close()
        logger.info(f"{self} disconnected.")


