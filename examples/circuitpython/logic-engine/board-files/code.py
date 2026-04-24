# Logic Engine — distance sensor + NeoPixel LED
# Connected Interaction Kit: ItsyBitsy M4 + Bitsy Expander
#
# Wiring:
#   VL53L0X distance sensor  →  any I2C header on Bitsy Expander
#   ChaiNEO NeoPixel LED      →  D7 header on Bitsy Expander

import gc
import time
import json
import board
import neopixel
import adafruit_vl53l0x
from MQTT import Create_MQTT
from settings import settings

gc.collect()

# ── Hardware ──────────────────────────────────────────────────────────

i2c = board.I2C()
tof = adafruit_vl53l0x.VL53L0X(i2c)

led = neopixel.NeoPixel(board.D7, 1, auto_write=False, pixel_order=neopixel.GRBW)
led.fill((0, 0, 0, 0))
led.show()

gc.collect()

# ── State ─────────────────────────────────────────────────────────────

distance = 500          # current sensor reading in mm
rules = []              # sorted by priority when program loads
default_actions = []    # applied when no rule matches

# ── LED output ────────────────────────────────────────────────────────

def set_led(r, g, b, br):
    led.brightness = max(0.0, min(1.0, br / 255.0))
    led.fill((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), 0))
    led.show()

def apply_actions(actions):
    for a in actions:
        if a["output"] == "led":
            v = a["values"]
            if len(v) >= 4:
                set_led(int(v[0]), int(v[1]), int(v[2]), int(v[3]))

# ── Condition evaluation ──────────────────────────────────────────────

def eval_check(op, thr):
    if op == "<":  return distance < thr
    if op == ">":  return distance > thr
    if op == "<=": return distance <= thr
    if op == ">=": return distance >= thr
    if op == "==": return distance == thr
    if op == "!=": return distance != thr
    return False

def rule_matches(rule):
    logic = rule["condition_logic"]
    for c in rule["checks"]:
        result = eval_check(c["op"], c["value"])
        if logic == "AND" and not result:
            return False        # short-circuit: one false kills AND
        if logic == "OR" and result:
            return True         # short-circuit: one true wins OR
    return logic == "AND"       # AND: all passed  /  OR: none passed

# ── MQTT message handler ──────────────────────────────────────────────

def on_message(client, topic, message):
    global rules, default_actions
    try:
        data = json.loads(message)
        gc.collect()
        prog = data.get("MQTT_value")
        if prog:
            raw = prog.get("rules", [])
            rules = sorted(raw, key=lambda r: r.get("priority", 99))
            default_actions = prog.get("default_actions", [])
            print("Program loaded:", len(rules), "rules")
        gc.collect()
    except Exception as e:
        print("Parse error:", e)
        gc.collect()

# ── MQTT setup ────────────────────────────────────────────────────────

client_id   = settings["mqtt_clientid"]
mqtt_topic  = settings.get("mqtt_topic", "logic-engine")
mqtt_client = Create_MQTT(client_id)
mqtt_client.on_message = on_message
mqtt_client.subscribe(mqtt_topic)
print("Ready on topic:", mqtt_topic)
gc.collect()

# ── Main loop ─────────────────────────────────────────────────────────

while True:
    try:
        mqtt_client.loop(timeout=0.05)

        try:
            d = tof.range
            if 50 <= d <= 950:
                distance = d
        except Exception:
            pass

        matched = False
        for rule in rules:
            if rule_matches(rule):
                apply_actions(rule["actions"])
                matched = True
                break

        if not matched:
            apply_actions(default_actions)

    except Exception as e:
        print("Loop error:", e)
        gc.collect()
        time.sleep(0.5)
