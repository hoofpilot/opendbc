from opendbc.car import Bus, structs
from opendbc.can import CANParser, CANDefine
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.interfaces import CarStateBase
from opendbc.car.byd.values import DBC, CANBUS

# Multiplier between GPS ground speed to the meter cluster's displayed speed
HUD_MULTIPLIER = 1.068


class CarState(CarStateBase):
  def __init__(self, CP, CP_SP):
    super().__init__(CP, CP_SP)
    can_define = CANDefine(DBC[CP.carFingerprint][Bus.pt])

    self.shifter_values = can_define.dv["GEAR_STATE"]["GEAR_STATE"]

  def update(self, can_parsers) -> tuple[structs.CarState, structs.CarStateSP]:
    cp = can_parsers[Bus.pt]
    ret = structs.CarState()
    ret_sp = structs.CarStateSP()

    ret.wheelSpeeds.fl = cp.vl["WHEEL_SPEEDS"]["WHEEL_FL"] * CV.KPH_TO_MS
    ret.wheelSpeeds.fr = cp.vl["WHEEL_SPEEDS"]["WHEEL_FR"] * CV.KPH_TO_MS
    ret.wheelSpeeds.rl = cp.vl["WHEEL_SPEEDS"]["WHEEL_RL"] * CV.KPH_TO_MS
    ret.wheelSpeeds.rr = cp.vl["WHEEL_SPEEDS"]["WHEEL_RR"] * CV.KPH_TO_MS
    ret.vEgoRaw = (ret.wheelSpeeds.rl + ret.wheelSpeeds.fl) / 2.0

    # unfiltered speed from CAN sensors
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.vEgoCluster = ret.vEgo * HUD_MULTIPLIER
    ret.standstill = ret.vEgoRaw < 0.01

    # safety checks to engage
    can_gear = int(cp.vl["GEAR_STATE"]["GEAR_STATE"])
    ret.gearShifter = self.parse_gear_shifter(self.shifter_values.get(can_gear, None))

    ret.doorOpen = any([cp.vl["SEATBELT"]["DOOR_RL_OPEN"],
                       cp.vl["SEATBELT"]["DOOR_FL_OPEN"],
                       cp.vl["SEATBELT"]["DOOR_RR_OPEN"],
                       cp.vl["SEATBELT"]["DOOR_FR_OPEN"]])

    ret.seatbeltUnlatched = cp.vl["SEATBELT"]["SEATBELT_DRIVER_LATCHED"] == 0

    ret.gas = cp.vl["PEDALS"]["GAS_PEDAL"] / 127.0
    ret.gasPressed = ret.gas > 1e-3

    ret.brakePressed = bool(cp.vl["BRAKE"]["BRAKE_PRESSED"]) or bool(cp.vl["PEDALS"]["BRAKE_PRESSED"])
    ret.brake = max(cp.vl["BRAKE_POSITION"]["BRAKE_POSITION"] / 511.0, 1.0 if ret.brakePressed else 0.0)
    ret.brakeLights = bool(cp.vl["LIGHTS"]["BRAKE_LIGHT"])

    # steer
    ret.steeringAngleDeg = cp.vl["STEER_ANGLE_SENSOR"]["STEER_RACK_ANGLE"]
    ret.steeringAngleOffsetDeg = cp.vl["NEW_MSG_1E2"]["STEER_ANGLE_2"] - ret.steeringAngleDeg
    ret.steeringTorque = cp.vl["STEER_ANGLE_SENSOR"]["STEER_TORQUE_MAG"]
    ret.steeringTorqueEps = cp.vl["ICC_STEERING"]["EPS_STEERING"]
    ret.steeringPressed = bool(ret.steeringTorqueEps > 6)
    ret.steerFaultTemporary = False
    ret.yawRate = cp.vl["YAW_RATE"]["YAW_RATE"] * CV.DEG_TO_RAD

    ret.stockAeb = False
    ret.stockFcw = False
    ret.cruiseState.available = bool(cp.vl["ICC_STATE"]["ICC_ON"]) or bool(cp.vl["ICC_STATE"]["ACC_ON"])
    ret.cruiseState.enabled = bool(cp.vl["ICC_STATE"]["ICC_ON"])

    ret.cruiseState.speedCluster = 0
    ret.cruiseState.speed = 0
    ret.cruiseState.standstill = ret.standstill
    ret.cruiseState.nonAdaptive = False

    ret.leftBlinker = bool(cp.vl["LIGHTS"]["LEFT_TURN"])
    ret.rightBlinker = bool(cp.vl["LIGHTS"]["RIGHT_TURN"])
    ret.genericToggle = bool(cp.vl["DRIVING_MODE_BUTTON"]["DRIVING_MODE_BUTTON_PRESSED"]) or bool(cp.vl["LIGHTS"]["BRIGHTS"])
    ret.espDisabled = False

    ret.leftBlindspot = False
    ret.rightBlindspot = False

    return ret, ret_sp

  @staticmethod
  def get_can_parsers(CP, CP_SP):
    pt_signals = [
      ("BRAKE_POSITION", 50),
      ("NEW_MSG_1E2", 50),
      ("WHEEL_SPEEDS", 50),
      ("BRAKE", 50),
      ("PEDALS", 50),
      ("SEATBELT", 20),
      ("STEER_ANGLE_SENSOR", 100),
      ("ICC_STEERING", 50),
      ("YAW_RATE", 50),
      ("ICC_STATE", 20),
      ("GEAR_STATE", 20),
      ("STEERING_WHEEL_BUTTONS", 20),
      ("LIGHTS", 20),
      ("IGNITION", 10),
      ("DRIVING_MODE_BUTTON", 20),
    ]

    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], pt_signals, CANBUS.main_bus),
    }
