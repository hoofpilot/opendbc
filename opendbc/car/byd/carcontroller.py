from opendbc.car.lateral import apply_std_steer_angle_limits, AngleSteeringLimits
from opendbc.car.interfaces import CarControllerBase
from opendbc.car import Bus


class CarControllerParams:
  ANGLE_LIMITS: AngleSteeringLimits = AngleSteeringLimits(
    220,
    ([0., 5., 15.], [4., 3., 2.]),
    ([0., 5., 15.], [6., 4., 3.]),
  )


class CarController(CarControllerBase):
  def __init__(self, dbc_names, CP, CP_SP):
    super().__init__(dbc_names, CP, CP_SP)
    self.apply_angle = 0

  def update(self, CC, CC_SP, CS, now_nanos):
    can_sends = []
    actuators = CC.actuators

    if (self.frame % 2) == 0:
      self.apply_angle = apply_std_steer_angle_limits(actuators.steeringAngleDeg, self.apply_angle,
      CS.out.vEgo, CS.out.steeringAngleDeg, CC.latActive, CarControllerParams.ANGLE_LIMITS)

    new_actuators = actuators.as_builder()
    new_actuators.steeringAngleDeg = self.apply_angle

    self.frame += 1
    return new_actuators, can_sends
