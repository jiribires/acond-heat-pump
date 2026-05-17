#!/usr/bin/env python3
"""
Diagnostic for set_summer_mode against a real Acond heat pump.

Reads every bit of TC_set (holding 40006) and TC_status (input 30007)
before and after calling set_summer_mode(False), so we can see whether:

  1. TC_set bit 8 actually flips (write reached the holding register), and
  2. TC_status bit 10 follows within the timeout (controller honored it).

Also dumps every other bit in both registers so any unexpected side-effect
on neighbouring control/status bits is visible.

Usage:
    python scripts/diag_summer_mode.py <host> [--enable-summer]

By default sets winter (summer=False). Pass --enable-summer to set summer.
"""

import argparse
import logging
import sys
import time

from acond_heat_pump import AcondHeatPump


TC_SET_BITS = {
    0: "automatic mode",
    1: "HP mode",
    2: "auxiliary heating mode",
    3: "off mode",
    4: "cooling mode",
    5: "fault acknowledgement",
    6: "solar on",
    7: "pool on",
    8: "summer/winter switching",
}

TC_STATUS_BITS = {
    0: "HP on",
    1: "HP operation",
    2: "HP in failure",
    3: "DHW heating",
    4: "circuit 1 heating",
    5: "circuit 2 heating",
    6: "solar circulation",
    7: "pool circulation",
    8: "defrosting",
    9: "E. Heater",
    10: "summer operation",
    11: "brine circulation",
    12: "cooling operation",
}


def dump_register(label, value, bit_labels):
    print(f"\n--- {label} ---")
    print(f"raw = 0x{value:04x}   binary = {value:016b}")
    for bit, name in bit_labels.items():
        on = bool(value & (1 << bit))
        print(f"  bit {bit:>2}: {'ON ' if on else 'off'}   {name}")


def read_tc_set(pump):
    r = pump.client.read_holding_registers(5, count=1, device_id=1)
    if r.isError():
        print("ERROR reading TC_set (holding 40006)")
        return None
    return r.registers[0]


def read_tc_status(pump):
    r = pump.client.read_input_registers(6, count=1, device_id=1)
    if r.isError():
        print("ERROR reading TC_status (input 30007)")
        return None
    return r.registers[0]


def snapshot(pump, when):
    print(f"\n========== {when} ==========")
    tc_set = read_tc_set(pump)
    if tc_set is not None:
        dump_register("TC_set (holding 40006)", tc_set, TC_SET_BITS)
    tc_status = read_tc_status(pump)
    if tc_status is not None:
        dump_register("TC_status (input 30007)", tc_status, TC_STATUS_BITS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Heat pump IP or hostname")
    parser.add_argument("--port", type=int, default=502)
    parser.add_argument(
        "--enable-summer",
        action="store_true",
        help="Set summer mode instead of winter (default: winter)",
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument(
        "--toggle-raw",
        action="store_true",
        help=(
            "Bypass set_summer_mode and write TC_set with bit 8 XOR'd from its "
            "current value, then poll TC_status. Tests whether TC_set bit 8 is "
            "edge-triggered."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    pump = AcondHeatPump(args.host, port=args.port)
    print(f"Connecting to {args.host}:{args.port} ...")
    if not pump.connect():
        print("Connection failed.")
        sys.exit(1)

    try:
        snapshot(pump, "BEFORE")

        if args.toggle_raw:
            current = read_tc_set(pump)
            baseline_status = read_tc_status(pump)
            if current is None or baseline_status is None:
                sys.exit(1)
            baseline_summer = bool(baseline_status & (1 << 10))
            new_value = current ^ (1 << 8)
            print(
                f"\n>>> Baseline status summer = {baseline_summer}"
            )
            print(
                f">>> Raw write: TC_set 0x{current:04x} -> 0x{new_value:04x} "
                f"(XOR bit 8)"
            )
            w = pump.client.write_register(5, new_value, device_id=1)
            print(f">>> write isError = {w.isError()}")
            print(
                f">>> Polling TC_status bit 10 for change from {baseline_summer} "
                f"for up to {args.timeout}s..."
            )

            deadline = time.monotonic() + args.timeout
            flipped = False
            while time.monotonic() < deadline:
                s = read_tc_status(pump)
                if s is not None:
                    cur = bool(s & (1 << 10))
                    if cur != baseline_summer:
                        flipped = True
                        print(f">>> status bit 10 flipped to {cur}")
                        break
                time.sleep(0.2)
            if not flipped:
                print(">>> status bit 10 did NOT flip within timeout")
        else:
            target = bool(args.enable_summer)
            print(
                f"\n>>> Calling set_summer_mode({target}) with timeout={args.timeout}s"
            )
            result = pump.set_summer_mode(target, timeout=args.timeout)
            print(f">>> returned: {result}")

        snapshot(pump, "AFTER")
    finally:
        pump.close()


if __name__ == "__main__":
    main()
