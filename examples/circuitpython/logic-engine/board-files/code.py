# Logic Engine — NeoPixel LED + Touch Sensor + Light Sensor
# Connected Interaction Kit: ItsyBitsy M4 + Bitsy Expander
#
# Wiring:
#   ChaiNEO NeoPixel LED  →  D7 header on Bitsy Expander
#   Touch sensor          →  D2 header on Bitsy Expander
#   Light sensor          →  A2 header on Bitsy Expander

import gc
import time
import json
import board
import digitalio
import analogio
import neopixel
from MQTT import Create_MQTT
from settings import settings

gc.collect()

# ── Hardware ──────────────────────────────────────────────────────────

led = neopixel.NeoPixel(board.D7, 1, auto_write=False, pixel_order=neopixel.GRB)
led.fill((0, 0, 0))
led.show()

touch_pin = digitalio.DigitalInOut(board.D2)
touch_pin.direction = digitalio.Direction.INPUT
touch_pin.pull = digitalio.Pull.DOWN

light_pin = analogio.AnalogIn(board.A2)

gc.collect()

# ── State ─────────────────────────────────────────────────────────────

inputs = {"touch": 0, "light": 0}
rules = []
default_actions = []
last_led = None
last_inputs_print = 0

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
        if a["output"] in ("led", "led_color"):
            v = a["values"]
            br = int(v[3]) if len(v) >= 4 else 255
            if len(v) >= 3:
                set_led(int(v[0]), int(v[1]), int(v[2]), br)

# ── Condition evaluation ──────────────────────────────────────────────

def eval_check(input_name, op, thr):
    val = inputs.get(input_name, 0)
    if op == "<":  return val < thr
    if op == ">":  return val > thr
    if op == "<=": return val <= thr
    if op == ">=": return val >= thr
    if op == "==": return val == thr
    if op == "!=": return val != thr
    return False

def rule_matches(rule):
    logic = rule["condition_logic"]
    for c in rule["checks"]:
        result = eval_check(c["input"], c["op"], c["value"])
        if logic == "AND" and not result:
            return False
        if logic == "OR" and result:
            return True
    return logic == "AND"

# ── MQTT message handler ──────────────────────────────────────────────

def on_message(client, topic, message):
    global rules, default_actions
    print("Message received:", message[:200])
    try:
        data = json.loads(message)
        gc.collect()
        raw = data.get("rules", [])
        rules = sorted(raw, key=lambda r: r.get("priority", 99))
        default_actions = data.get("default_actions", [])
        print("Program loaded:", len(rules), "rules,", len(default_actions), "defaults")
        for i, r in enumerate(rules):
            print("  rule", i, r.get("label"), r.get("checks"))
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

        inputs["touch"] = 1 if touch_pin.value else 0
        inputs["light"] = light_pin.value

        # Print sensor values every 2 seconds for calibration
        now = time.monotonic()
        if now - last_inputs_print >= 2.0:
            print("touch:", inputs["touch"], "| light:", inputs["light"])
            last_inputs_print = now

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
