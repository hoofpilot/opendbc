#pragma once
#include "opendbc/safety/declarations.h"

static bool byd_longitudinal = false;

static void byd_rx_hook(const CANPacket_t *to_push) {
  int bus = GET_BUS(to_push);
  int addr = GET_ADDR(to_push);
  
  if (bus == 0) {
    // Steering angle
    if (addr == 287) {
      int angle_meas_new = (GET_BYTES(to_push, 0, 2) & 0xFFFFU);
      angle_meas_new = to_signed(angle_meas_new, 16);
      update_sample(&angle_meas, angle_meas_new);
    }

    // Gas and brake
    if (addr == 834) {
      gas_pressed = (GET_BYTE(to_push, 0) > 0U);
      brake_pressed = (GET_BYTE(to_push, 1) > 0U);
    }

    // Wheel speeds
    if (addr == 496) {
      uint16_t fl_ms = ((GET_BYTE(to_push, 1) & 0x000FU) << 8) | (GET_BYTE(to_push, 0));
      uint16_t br_ms = ((GET_BYTE(to_push, 6) & 0x000FU) << 8) | (GET_BYTE(to_push, 5));
      vehicle_moving = (fl_ms | br_ms) != 0U;
      UPDATE_VEHICLE_SPEED((fl_ms + br_ms) / 2.0 * 0.1 * KPH_TO_MS);
    }
    
    // ICC/ACC state for controls_allowed
    if (addr == 508) {
      // ICC_STEERING_STATE on bit 1
      bool icc_steering = GET_BIT(to_push, 1);
      controls_allowed = icc_steering;
    }
  }
}

static bool byd_tx_hook(const CANPacket_t *to_send) {
  SAFETY_UNUSED(to_send);
  // Allow all for now - we are not sending anything anyway
  return true;
}

static safety_config byd_init(uint16_t param) {
  SAFETY_UNUSED(param);
  byd_longitudinal = false;
  controls_allowed = 0;  // Start with controls disabled
  
  static const CanMsg BYD_TX_MSGS[] = {
    {482, 0, 8, .check_relay = false},
    {790, 0, 8, .check_relay = false},
  };

  static RxCheck byd_rx_checks[] = {
    {.msg = {{287, 0, 5, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true, .frequency = 100U}, { 0 }, { 0 }}},
    {.msg = {{496, 0, 8, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true, .frequency = 50U}, { 0 }, { 0 }}},
    {.msg = {{508, 0, 8, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true, .frequency = 20U}, { 0 }, { 0 }}},
    {.msg = {{834, 0, 8, .ignore_checksum = true, .ignore_counter = true, .ignore_quality_flag = true, .frequency = 50U}, { 0 }, { 0 }}},
  };
  
  return BUILD_SAFETY_CFG(byd_rx_checks, BYD_TX_MSGS);
}

const safety_hooks byd_hooks = {
  .init = byd_init,
  .rx = byd_rx_hook,
  .tx = byd_tx_hook,
};
