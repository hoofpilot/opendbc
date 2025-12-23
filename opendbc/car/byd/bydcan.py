def create_can_steer_command(packer, steer_angle, steer_req, is_standstill, counter):
  # keep the legacy standstill behavior to match earlier tuning
  set_me_xe = 0xE if is_standstill else 0xB

  values = {
    "STEER_REQ": steer_req,
    "STEER_ANGLE": steer_angle,
    "SET_ME_XE": set_me_xe if steer_req else 0,
    "SET_ME_FF": 0xFF,
    "SET_ME_F": 0xF,
    "SET_ME_1_1": 1,
    "SET_ME_1_2": 1,
    "SET_ME_X01": 1,
    # keep EPS_OK asserted when commanding; set zero if we need to drop torque
    "EPS_OK": 1 if steer_req else 0,
    "UNKNOWN": 0,
    "COUNTER": counter & 0xF,
    "CHECKSUM": 0,
  }

  return packer.make_can_msg("STEERING_MODULE_ADAS", 0, values)

def create_accel_command(packer, accel, enabled, brake_hold, counter):
  accel = max(min(accel * 13, 30), -50)
  accel_factor = 12 if accel >= 2 else 5 if accel < 0 else 11
  enabled &= not brake_hold

  if brake_hold:
    accel = 0

  values = {
    "ACCEL_CMD": accel,
    # always 25
    "SET_ME_25_1": 25,
    "SET_ME_25_2": 25,
    "ACC_ON_1": enabled,
    "ACC_ON_2": enabled,
    # some unknown state, 12 when accel, below 11 when braking, 11 when cruising
    "ACCEL_FACTOR": accel_factor if enabled else 0,
    # some unknown state, 0 when not engaged, 3/4 when accel, 8/9 when accel uphill, 1 when braking (all speculation)
    "DECEL_FACTOR": 8 if enabled else 0,
    "SET_ME_X8": 8,
    "SET_ME_1": 1,
    "SET_ME_XF": 0xF,
    "CMD_REQ_ACTIVE_LOW": 0 if enabled else 1,
    "ACC_REQ_NOT_STANDSTILL": enabled,
    "ACC_CONTROLLABLE_AND_ON": enabled,
    "ACC_OVERRIDE_OR_STANDSTILL": brake_hold,
    "STANDSTILL_STATE": brake_hold,
    "STANDSTILL_RESUME": 0,
    "COUNTER": counter & 0xF,
    "CHECKSUM": 0,
  }

  return packer.make_can_msg("ACC_CMD", 0, values)

def create_lkas_hud(packer, hud_tsr, settings, enabled, lka_on, counter):
  # populate only the known safety critical bits; leave visuals minimal
  steer_active_low = 0 if (enabled and lka_on) else 1

  values = {
    "SETTINGS": settings,
    "TSR": hud_tsr,
    "HAND_ON_WHEEL_WARNING": 0,
    "LKAS_ENABLED": 1 if lka_on else 0,
    "STEER_ACTIVE_ACTIVE_LOW": steer_active_low,
    "LEFT_LANE_VISIBLE": 1 if enabled else 0,
    "RIGHT_LANE_VISIBLE": 1 if enabled else 0,
    "LSS_STATE": 0,
    "HMA": 0,
    "PT2": 0,
    "PT3": 0,
    "PT4": 0,
    "PT5": 0,
    "TSR_STATUS": 0,
    "SET_ME_XFF": 0xFF,
    "SET_ME_1_2": 1,
    "COUNTER": counter & 0xF,
    "CHECKSUM": 0,
  }

  return packer.make_can_msg("LKAS_HUD_ADAS", 0, values)

def send_buttons(packer, state):
  values = {
    "SET_BTN": state,
    "RES_BTN": state,
    "SET_ME_1_1": 1,
    "SET_ME_1_2": 1,
  }
  return packer.make_can_msg("PCM_BUTTONS", 0, values)




def byd_checksum(address: int, sig, d: bytearray) -> int:
  byte_key = 0xAF

  sum_first = 0
  sum_second = 0

  # skip checksum at the last byte
  for b in d[:-1]:
    sum_first += b >> 4
    sum_second += b & 0xF

  remainder = (sum_second >> 4) & 0xFF
  sum_first += (byte_key & 0xF)
  sum_second += (byte_key >> 4)

  inv_first = (-sum_first + 0x9) & 0xF
  inv_second = (-sum_second + 0x9) & 0xF

  checksum = (((inv_first + (5 - remainder)) << 4) + inv_second) & 0xFF
  return checksum
