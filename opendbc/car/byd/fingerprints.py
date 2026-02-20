# ruff: noqa: E501

""" AUTO-FORMATTED USING opendbc/car/debug/format_fingerprints.py, EDIT STRUCTURE THERE."""
from opendbc.car.structs import CarParams
from opendbc.car.byd.values import CAR

# Fingerprint derived from real BYD Sealion 7 routes (bus 0 + bus 2 union).
# 7 routes analysed: 77f37d19ff (35 segs), ad6180ee33 (5 segs), 7d9990006e (1 seg),
#   c44d4966f2 (14 segs), 83525d8527 (2 segs), cae092ad9a (31 segs), b60a02b231 (10 segs).
# Threshold: ID must appear in ≥2 routes OR have ≥30 total messages across all routes.
FINGERPRINTS = {
  CAR.BYD_SEALION: [{
    140: 8, 213: 8, 287: 5, 289: 8, 291: 8, 301: 8, 307: 8, 311: 8, 312: 8, 337: 8, 359: 8,
    482: 8, 493: 8, 496: 8, 508: 8, 511: 8, 536: 8, 537: 8, 544: 8, 546: 8, 547: 8, 567: 8,
    575: 8, 576: 8, 578: 8, 588: 8, 604: 8, 626: 8, 657: 8, 660: 8, 661: 8, 663: 8, 668: 8,
    692: 8, 714: 8, 748: 8, 758: 8, 790: 8, 796: 64, 798: 8, 801: 8, 802: 8, 803: 8, 813: 8,
    814: 8, 815: 8, 833: 8, 834: 8, 835: 8, 836: 8, 837: 8, 854: 8, 860: 8, 877: 8, 905: 8,
    906: 8, 940: 8, 944: 8, 948: 8, 951: 8, 965: 8, 973: 8, 985: 8, 1023: 8, 1028: 8, 1031: 8,
    1033: 8, 1040: 8, 1048: 8, 1050: 8, 1058: 8, 1074: 8, 1092: 8, 1093: 8, 1107: 8, 1108: 8,
    1141: 8, 1166: 8, 1168: 8, 1178: 8, 1189: 8, 1203: 64, 1204: 64, 1226: 64, 1246: 8,
    1279: 8, 1297: 8, 1298: 8, 1319: 8, 1322: 8, 1365: 8, 1366: 8, 1382: 8
  }],

}

Ecu = CarParams.Ecu

FW_VERSIONS = {
  CAR.BYD_SEALION: {
    (Ecu.hvac, 0x7b3, None): [
      b'\xf1\x8b\x00\x00\x00\xff',
    ],
    (Ecu.engine, 0x7e0, None): [
      b'H7\x00\x11V\xfd\x00\x12!',
    ],
  },
}
