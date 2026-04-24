# Companion Description — Logic Engine (distance + LED)

## What this setup is

A Raspberry Pi Pico 2W with one input and one output:
- **Distance sensor** (VL53L0X, I²C): measures how far away the nearest object is, 50–950 mm
- **NeoPixel LED** (ChaiNEO, D7): a single full-colour RGB LED

The device runs a logic program written by the LLM in real time. When you describe a behaviour in the chat, the LLM writes a new program and sends it to the device via MQTT. The device then evaluates the program against live sensor readings continuously — no further LLM calls are needed until you change the behaviour again.

---

## How to set up in the webapp

1. Create a new assistant in the Prompting Realities webapp
2. Paste the contents of `system_prompt.md` into the **Instruction** field
3. Paste the contents of `logic_schema.json` into the **JSON Schema** field
4. Enter your MQTT broker credentials and set the topic to match `settings.py`
5. Start a session and share the link

---

## Test sequence — from simple to complex

Work through these prompts in order. Each one exercises a different logic type. Observe the LED response and note what the device does.

### 1. Direct output — baseline state
> *"Make the LED glow soft blue."*

Expected: LED turns on in a calm blue colour. No conditions — the LLM sets a `default_action`. Good starting point to confirm the pipeline is working end to end.

---

### 2. Single threshold rule — on/off
> *"When something gets close — within about 20 cm — turn the LED red. Otherwise keep it off."*

Expected: LED is off when nothing is near; turns red when an object is within ~200 mm. Tests basic conditional rule.

Try: slowly move your hand toward the sensor and watch the LED switch.

---

### 3. Distance zones — multiple rules
> *"Show three distance zones with colour: red when very close (under 15 cm), yellow in the middle (15–40 cm), and green when far. Off when nothing is in range."*

Expected: three distinct colour bands as you move closer/further. Tests priority-ordered rules — the LLM should write three rules with ascending priorities so the closest match wins.

---

### 4. Proportional mapping — brightness
> *"Map the distance to the LED brightness — bright when something is close, dim when it's far away."*

Expected: the LED intensity changes smoothly and continuously as you move your hand. Tests the `mappings` logic type. The colour should stay fixed; only brightness changes.

---

### 5. Proportional mapping — colour channel
> *"Keep the LED at full brightness, but map the distance to colour — red when close, fading to blue as you move away."*

Expected: smooth colour shift between red and blue as a function of distance. The LLM needs to map distance onto the R channel (close = high R, far = low R) and the B channel (close = low B, far = high B) simultaneously. Tests two mappings working together.

---

### 6. Triggered sequence — animation on event
> *"When I get very close — within 10 cm — flash the LED white three times, then go back to off."*

Expected: LED stays off normally; when you bring your hand within ~100 mm, it flashes white three times and stops. Tests the `sequences` logic type with a condition trigger and finite repeat.

Try: approach slowly and see at what distance the flash triggers. Move away and approach again — it should retrigger.

---

### 7. Combined — mapping + override rule
> *"Continuously map the distance to LED brightness so it glows brighter as you approach. But if you get closer than 5 cm, switch to a fast red pulse — like an alarm."*

Expected: smooth brightness ramp on approach; alarm sequence triggers if you get within ~50 mm. Tests mappings and sequences coexisting, with the sequence taking over when the extreme threshold is crossed.

---

### 8. Open-ended exploration
Now that the basic types work, explore what the LLM can and cannot do:

- *"Make the LED breathe slowly — fade in and out on its own."* (ALWAYS sequence, no trigger condition)
- *"Use the distance to mix between green and purple."* (mapping two channels at once)
- *"Create a calming effect — the closer you are, the slower and warmer the colour."* (intentionally vague — see how the LLM interprets it)
- *"When something is between 20 and 40 cm away, glow orange. Ignore everything else."* (compound AND condition with two checks)
- Something you come up with yourself

---

## What to observe and note

- **Threshold precision**: how accurately does the LLM translate "20 cm" into a mm value?
- **Behaviour continuity**: do rules and mappings interact cleanly, or do you notice flickering/conflicts?
- **Sequence re-triggering**: does the flash sequence restart correctly after the condition goes false and true again?
- **LLM interpretation of vague prompts**: when you describe something poetic or non-technical, what choices does the LLM make?
- **Limits**: what kind of request does the LLM fail to express within the schema? (e.g. "remember the last position", "react to the speed of movement")

---

## Extending this setup

Once this works, the natural next steps are:

- **Add a second input** (e.g. touch pad, sound sensor) to explore compound conditions across two sensors
- **Add a second output** (e.g. buzzer) and test whether the LLM can coordinate two outputs in a single program
- **Adjust the schema** to add new logic types (e.g. hysteresis, time-based events)
