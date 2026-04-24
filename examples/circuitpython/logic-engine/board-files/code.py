# Logic Engine — NeoPixel LED
# Connected Interaction Kit: ItsyBitsy M4 + Bitsy Expander
#
# Wiring:
#   ChaiNEO NeoPixel LED  →  D7 header on Bitsy Expander
#
# Note: ToF distance sensor disabled — adafruit_vl53l0x + adafruit_minimqtt
#       exceed 192KB RAM together. Use .mpy compiled lib to re-enable.

import gc
import time
import json
import board
import neopixel
from MQTT import Create_MQTT
from settings import settings

gc.collect()

# ── Hardware ──────────────────────────────────────────────────────────

led = neopixel.NeoPixel(board.D7, 1, auto_write=False, pixel_order=neopixel.GRB)
led.fill((0, 0, 0))
led.show()

gc.collect()

# ── State ─────────────────────────────────────────────────────────────

distance = 500
rules = []
default_actions = []
last_led = None

# ── LED output ────────────────────────────────────────────────────────

def set_led(r, g, b, br):
    global last_led
    vals = (r, g, b, br)
    if vals != last_led:
        if r > 0 or g > 0 or b > 0 or br > 0:
            print("LED:", r, g, b, "brightness:", br)
        else:
            print("LED: off")
        last_led = vals
    led.brightness = max(0.0, min(1.0, br / 255.0))
    led.fill((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
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
            return False
        if logic == "OR" and result:
            return True
    return logic == "AND"

# ── MQTT message handler ──────────────────────────────────────────────

def on_message(client, topic, message):
    global rules, default_actions
    print("Message received:", message[:80])
    try:
        data = json.loads(message)
        gc.collect()
        # Webapp publishes MQTT_value contents directly, so rules/default_actions
        # are at the top level of the received message
        raw = data.get("rules", [])
        rules = sorted(raw, key=lambda r: r.get("priority", 99))
        default_actions = data.get("default_actions", [])
        print("Program loaded:", len(rules), "rules,", len(default_actions), "defaults")
        apply_actions(default_actions)
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
        mqtt_client.loop(timeout=0.2)

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
