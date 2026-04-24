# Logic Engine — distance sensor + NeoPixel LED
# Connected Interaction Kit: ItsyBitsy M4 + Bitsy Expander
#
# Wiring:
#   VL53L0X distance sensor  →  any I2C header on Bitsy Expander
#   ChaiNEO NeoPixel LED      →  D7 header on Bitsy Expander
#
# Receives a JSON "program" from the LLM via MQTT.
# Evaluates rules, mappings and sequences against live sensor readings every ~50ms.
# Each new program fully replaces the previous one.

import time
import json
import board
import neopixel
import adafruit_vl53l0x
from MQTT import Create_MQTT
from settings import settings

# ── Hardware init ─────────────────────────────────────────────────────

i2c = board.I2C()
tof = adafruit_vl53l0x.VL53L0X(i2c)

led = neopixel.NeoPixel(board.D7, 1, auto_write=False, pixel_order=neopixel.GRBW)
led.fill((0, 0, 0, 0))
led.show()

# ── State ─────────────────────────────────────────────────────────────

inputs = {"distance": 500}

output_state = {"led": [0, 0, 0, 0]}   # [R, G, B, brightness]
last_pushed  = {"led": None}            # tracks last value sent to hardware

program = None   # current logic program from LLM

# Sequence playback state (one active sequence at a time)
active_sequence  = None
seq_step_index   = 0
seq_step_start   = 0.0
seq_repeat_count = 0

# ── Input reading ─────────────────────────────────────────────────────

def read_inputs():
    try:
        d = tof.range
        if 50 <= d <= 950:          # filter unreliable out-of-range values
            inputs["distance"] = d
    except Exception as e:
        print("ToF read error:", e)

# ── Output dispatch ───────────────────────────────────────────────────

def push_output(name):
    vals = output_state.get(name)
    if not vals:
        return
    if last_pushed.get(name) == vals:
        return                       # no change, skip hardware write
    last_pushed[name] = list(vals)
    if name == "led":
        r  = max(0, min(255, int(vals[0])))
        g  = max(0, min(255, int(vals[1])))
        b  = max(0, min(255, int(vals[2])))
        br = max(0, min(255, int(vals[3])))
        led.brightness = br / 255.0
        led.fill((r, g, b, 0))
        led.show()

def apply_actions(actions):
    for a in actions:
        name = a.get("output")
        vals = a.get("values")
        if name in output_state and vals:
            output_state[name] = list(vals)
            push_output(name)

def apply_single_channel(name, channel, value):
    ch = int(channel)
    if name in output_state and ch < len(output_state[name]):
        output_state[name][ch] = value
        push_output(name)

# ── Condition evaluation ──────────────────────────────────────────────

def eval_check(check):
    val = inputs.get(check["input"], 0)
    op  = check["op"]
    thr = check["value"]
    if op == "<":  return val < thr
    if op == ">":  return val > thr
    if op == "<=": return val <= thr
    if op == ">=": return val >= thr
    if op == "==": return val == thr
    if op == "!=": return val != thr
    return False

def eval_condition(logic, checks):
    if not checks:
        return False
    results = [eval_check(c) for c in checks]
    return all(results) if logic == "AND" else any(results)

# ── Mappings ──────────────────────────────────────────────────────────

def apply_mappings():
    for m in program.get("mappings", []):
        raw  = inputs.get(m["input"], m["in_min"])
        span = m["in_max"] - m["in_min"]
        ratio = 0.0 if span == 0 else (raw - m["in_min"]) / span
        ratio = max(0.0, min(1.0, ratio))
        mapped = m["out_min"] + ratio * (m["out_max"] - m["out_min"])
        apply_single_channel(m["output"], m["output_channel"], mapped)

# ── Rules ─────────────────────────────────────────────────────────────

def apply_rules():
    rules = sorted(program.get("rules", []), key=lambda r: r.get("priority", 99))
    for rule in rules:
        if eval_condition(rule["condition_logic"], rule["checks"]):
            apply_actions(rule["actions"])
            return True
    return False

# ── Sequences ─────────────────────────────────────────────────────────

def start_sequence(seq):
    global active_sequence, seq_step_index, seq_step_start, seq_repeat_count
    if not seq.get("steps"):
        return
    active_sequence  = seq
    seq_step_index   = 0
    seq_repeat_count = 0
    apply_actions(seq["steps"][0]["actions"])
    seq_step_start = time.monotonic()
    print("Sequence started:", seq.get("label", ""))

def tick_sequence(now):
    global active_sequence, seq_step_index, seq_step_start, seq_repeat_count
    if active_sequence is None:
        return
    steps = active_sequence["steps"]
    if now - seq_step_start < steps[seq_step_index]["duration"]:
        return                       # current step still running
    seq_step_index += 1
    if seq_step_index >= len(steps):
        seq_repeat_count += 1
        repeat = active_sequence.get("repeat", 1)
        # repeat == 0 means infinite; ALWAYS trigger also loops forever
        infinite = (repeat == 0) or (active_sequence.get("trigger_condition_logic") == "ALWAYS")
        if infinite or seq_repeat_count < repeat:
            seq_step_index = 0      # loop back to first step
        else:
            active_sequence = None  # sequence finished
            print("Sequence finished")
            return
    apply_actions(steps[seq_step_index]["actions"])
    seq_step_start = now

def check_sequences():
    if active_sequence is not None:
        return                       # don't interrupt a running sequence
    for seq in program.get("sequences", []):
        trigger = seq.get("trigger_condition_logic", "AND")
        if trigger == "ALWAYS":
            start_sequence(seq)
            return
        if eval_condition(trigger, seq.get("trigger_checks", [])):
            start_sequence(seq)
            return

# ── MQTT message handler ──────────────────────────────────────────────

def on_message(client, topic, message):
    global program, active_sequence
    try:
        data = json.loads(message)
        prog = data.get("MQTT_value")
        if prog is not None:
            program = prog
            active_sequence = None   # cancel any running sequence
            print("New program loaded")
        else:
            print("Received message without 'MQTT_value' key")
    except Exception as e:
        print("Parse error:", e)

# ── MQTT setup ────────────────────────────────────────────────────────

client_id   = settings["mqtt_clientid"]
mqtt_topic  = settings.get("mqtt_topic", "logic-engine")
mqtt_client = Create_MQTT(client_id)
mqtt_client.on_message = on_message
mqtt_client.subscribe(mqtt_topic)
print("Subscribed to:", mqtt_topic)

# ── Main loop ─────────────────────────────────────────────────────────
#
# Priority per tick (last write wins):
#   1. default_actions  — baseline state
#   2. mappings         — continuous proportional overrides
#   3. rules            — first matching rule overrides everything
#
# Sequences suspend rules/mappings while running.

while True:
    now = time.monotonic()
    try:
        mqtt_client.loop(timeout=0.05)
        read_inputs()

        if active_sequence is not None:
            tick_sequence(now)
        else:
            check_sequences()
            if program:
                apply_actions(program.get("default_actions", []))
                apply_mappings()
                apply_rules()

    except Exception as e:
        print("Loop error:", e)
        time.sleep(0.5)
