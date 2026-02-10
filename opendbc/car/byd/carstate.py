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
    self.hud_passthrough = 0
    self.adas_settings_pt = 0
    self.lka_on = 0
    self.eps_ok = 0

  def update(self, can_parsers) -> tuple[structs.CarState, structs.CarStateSP]:
    cp = can_parsers[Bus.pt]
    cp_cam = can_parsers[Bus.cam]
    ret = structs.CarState()
    ret_sp = structs.CarStateSP()

    self.adas_settings_pt = cp_cam.vl["LKAS_HUD_ADAS"]["SETTINGS"]
    self.hud_passthrough = cp_cam.vl["LKAS_HUD_ADAS"]["TSR"]
    self.lka_on = cp_cam.vl["LKAS_HUD_ADAS"]["LKAS_ENABLED"]
    self.eps_ok = cp_cam.vl["STEERING_MODULE_ADAS"]["EPS_OK"]

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

    # Gas position isn't in this DBC snapshot.
    ret.gasPressed = False

    ret.brakePressed = bool(cp.vl["BRAKE"]["BRAKE_PRESSED"])
    ret.brake = 1.0 if ret.brakePressed else 0.0

    # steer
    ret.steeringAngleDeg = cp.vl["STEER_ANGLE_SENSOR"]["STEER_RACK_ANGLE"]
    ret.steeringTorque = cp.vl["STEER_ANGLE_SENSOR"]["STEER_TORQUE_MAG"]
    ret.steeringTorqueEps = ret.steeringTorque
    ret.steeringPressed = bool(ret.steeringTorqueEps > 6)
    ret.steerFaultTemporary = not bool(self.eps_ok)

    ret.stockAeb = False
    ret.stockFcw = False
    ret.cruiseState.available = bool(cp_cam.vl["ACC_HUD_ADAS"]["ACC_ON1"]) or bool(cp_cam.vl["ACC_HUD_ADAS"]["ACC_ON2"])
    if ret.cruiseState.available:
      ret.cruiseState.speedCluster = max(int(cp_cam.vl["ACC_HUD_ADAS"]["SET_SPEED"]), 30) * CV.KPH_TO_MS
    else:
      ret.cruiseState.speedCluster = 0
    ret.cruiseState.speed = ret.cruiseState.speedCluster / HUD_MULTIPLIER
    ret.cruiseState.standstill = bool(cp_cam.vl["ACC_CMD"]["STANDSTILL_STATE"])
    ret.cruiseState.nonAdaptive = False
    ret.cruiseState.enabled = not bool(cp_cam.vl["ACC_CMD"]["CMD_REQ_ACTIVE_LOW"])

    ret.leftBlinker = bool(cp.vl["LIGHTS"]["LEFT_TURN"])
    ret.rightBlinker = bool(cp.vl["LIGHTS"]["RIGHT_TURN"])
    ret.genericToggle = False
    ret.espDisabled = False

    ret.leftBlindspot = False
    ret.rightBlindspot = False

    return ret, ret_sp

  @staticmethod
  def get_can_parsers(CP, CP_SP):
    pt_signals = [
      ("WHEEL_SPEEDS", 50),
      ("BRAKE", 50),
      ("SEATBELT", 20),
      ("STEER_ANGLE_SENSOR", 100),
      ("GEAR_STATE", 20),
      ("LIGHTS", 20),
    ]

    cam_signals = [
      ("ACC_HUD_ADAS", 50),
      ("ACC_CMD", 50),
      ("LKAS_HUD_ADAS", 50),
      ("STEERING_MODULE_ADAS", 50),
    ]

    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], pt_signals, CANBUS.main_bus),
      Bus.cam: CANParser(DBC[CP.carFingerprint][Bus.cam], cam_signals, CANBUS.cam_bus),
    }
