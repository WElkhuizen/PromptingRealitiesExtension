content = """# Project Report: Pico Logic Engine & AI Assistant

## 1. The Project Concept
The goal is to create an interactive and smart hardware system using a **Raspberry Pi Pico 2W**. Instead of hardcoding the behaviors, the system operates via a **Logic Engine** driven by an AI (LLM). 
The user talks to the AI, gives it the components it has plugged and the pins it has plugged them on, the AI generates a structured JSON file, and the Pico interprets it live via **MQTT** to link sensors (inputs) to actuators (outputs).

**Hardware:**
*   **Dynamic Configuration:** Instead of a fixed wiring diagram, the system now supports dynamic pin assignment. The AI identifies the hardware layout (Grove ports like D16, A0, I2C) through a "Handshake" conversation with the user.
*   **Inputs/Outputs:** Supports Touch, Light, Temp, Distance (Inputs) and NeoPixels, Piezo, Servo (Outputs).

---

## 2. The Logic Engine Architecture (JSON)
To allow the AI to control the Pico without breaking everything, we use a JSON structure divided into three core pillars:
1.  **`default_actions` (The Base State):** Defines the state of each output when nothing else is happening. Crucial for setting the target color of an LED before you can map its brightness.
2.  **`rules` (Discrete States):** Operate using conditions (`<`, `>`, `==`) and are evaluated by **priority**. Ideal for triggers (e.g., "If touched, ring the alarm") or fixed states ("If temp < 30000, turn Blue").
3.  **`mappings` (Continuous Logic):** Interpolate a sensor value to an output (using a `map()` function). Ideal for fading, nightlights, or a Theremin (distance = sound frequency).

---

## 3. Bugs Encountered and Solutions Found
### Bug 1: The Silent Theremin (Rule vs. Mapping Conflict)
*   **The Problem:** The user wanted the Piezo to play a sound based on distance (Mapping), but wanted it muted if the touch sensor wasn't being touched (Rule).
*   **The Solution:** Modifying the Python code on the Pico. I added a check: if the Rule sends an empty frequency array `[]`, it means it doesn't want to take control of the notes, allowing the distance Mapping to override it.

### Bug 2: The "Off" LED2 (The RGB Channel Trap)
*   **The Problem:** The AI tried to map temperature to the Red channel, but used values too low to be visible, and it failed to handle multi-color transitions.
*   **The Solution:** Strictly forbidding the AI from using `mappings` to change colors. Colors linked to temperature **must** be handled via `rules` using absolute color values (e.g., Blue = `[[0, 0, 255, 0]]`).

### Bug 3: The Nightlight Bug (Inverted Logic)
*   **The Problem:** The AI mapped high light values to high brightness (the opposite of a nightlight).
*   **The Solution:** Added a specific rule in the prompt forcing the AI to invert `out_min` and `out_max` for light-sensitive behaviors.

### Bug 4: The "Untouched" Priority Trap (Rule vs. Mapping)
*   **The Problem:** The user wanted an LED to act as a nightlight (brightness mapped to light sensor) while remaining green. The AI created an "untouched" rule (touch == 0) to set the LED to green. However, because Rules have a higher priority than Mappings in the logic engine, the rule was constantly "locking" the LED, preventing the mapping from updating the brightness.
*   **The Solution:** Forbidding the AI from creating rules for "idle" or "normal" states (like touch == 0). Instead, the "normal" color must be defined in default_actions, which has the lowest priority, allowing the mapping to modify its brightness.

### Bug 5: The "Brightness of Black" Logical Fallacy
*   **The Problem:** The AI attempted to map brightness (channel 4) to an LED that was set to [[0, 0, 0, 0]] (Off/Black) in the default state. In the logic engine, brightness is a multiplier; multiplying "nothing" by any value still results in "nothing".
*   **The Solution:** Training the AI to always check if a target color is defined in default_actions before applying a brightness mapping. If you want a "Green Nightlight," the base state must be Green, not Black.

---

## 4. The User Interface (UX/UI)
The web interface was designed to be both functional and aesthetically pleasing, using a "Petal & Bordeaux" color palette.
*   **The Chat Interface:** Uses a responsive layout with distinct bubble styles. User messages appear in "Bordeaux" (#4a1523), while AI responses are in "Petal Pink" (#f4a7bb).
*   **Control Center:** Added a persistent header with a "Reset" function to clear the logic and history, allowing for quick iteration on hardware experiments.
*   **Caching & Optimization:** Implementation of versioning for CSS/JS assets to ensure the latest UI improvements (like button centering and color tweaks) are delivered instantly without cache conflicts.

---

## 5. Connectivity & Protocol (MQTT & WiFi)
To make the system robust and multi-user friendly, the communication layer was overhauled:
*   **Unique Identification:** Each Pico is assigned a unique ID. MQTT topics are now structured as `toolkit/{ID}/command` for sending the JSON to the board or `toolkit/{ID}/sensors` for receiving the data of the sensors from the board, ensuring that logic intended for one device doesn't accidentally trigger another on the same network.
*   **WiFi Portal:** The system now handles the initial connection via a dedicated portal but it has to be opened manually by typing the ip address in a browser after connecting to the "Toolkit_Assistant" network. It seems to be impossible to make a pop-up open because every device (computer or phone) detects that it is not a real wifi.
*   **Persistence:** The UI fetches conversation history from the server on load, allowing the user to refresh the page without losing the current hardware configuration context.

---

## 6. The Evolution of the System Prompt
0.  **The First Message Protocol (Hardware Discovery):** To make the system universal, I implemented a "Zero-Knowledge" start. The AI is strictly forbidden from generating logic until the user defines the hardware setup. It starts by asking: "Which components have you plugged in and on which ports?". This ensures the `hardware_config` in the JSON perfectly matches the physical reality of the user's board.
1.  **Strict Formatting:** Mandatory 5-key structure for all action objects to ensure the Python parser never crashes.
2.  **The 10-Point Survival Checklist:** A final verification step (increased from 9 to 10 points) that forces the AI to double-check for "logical deadlocks" before sending the JSON.
3.  **Priority Hierarchy Awareness:** The prompt now explicitly teaches the AI the engine's internal hierarchy: Rules > Mappings > Default Actions. This prevents the AI from creating a high-priority rule that accidentally "crushes" a background mapping.
4.  **The "Untouched" Rule Prohibition:** To solve the nightlight conflict, the prompt now forbids "idle state" rules (e.g., touch == 0). It forces the AI to use `default_actions` for the base state, keeping the "logical space" free for mappings.
5.  **Learning by Example:** Inclusion of 5 specialized JSON templates (Theremin, Color steps, Nightlight + Touch alert) to guide the AI through complex multi-sensor scenarios.
6.  **Cumulative State:** Forcing the AI to remember and merge previous behaviors instead of resetting the device every turn, allowing for a truly additive building experience.

---

## 7. Hardware Limitation: BLE Scanning and Estimote Stickers
**BLE Integration for Context-Aware Inputs:**
To extend the system beyond direct physical sensors, I attempted to integrate **Bluetooth Low Energy (BLE)** scanning in order to detect **Estimote Stickers**. These devices broadcast contextual data (temperature, motion, acceleration) via BLE advertisement packets, which could serve as wireless inputs for the Logic Engine.
The goal was to treat these stickers as additional dynamic inputs (`sticker_temp`, `sticker_accel`, `sticker_moving`).

However, this revealed a limitation of the **Raspberry Pi Pico 2W**. Its BLE support—both in CircuitPython and MicroPython—is partial and not suited for continuous low-level scanning. In particular, accessing and reliably parsing **manufacturer data** from advertisement packets is unstable.

I considered and started switching from **CircuitPython** to **MicroPython**, but this does not solve the issue, as both rely on the same underlying hardware (**CYW43439 chip**) and BLE stack.

As a result, the Pico 2W cannot reliably detect Estimote Stickers in real time, limiting the system to wired sensors.

**Future direction:** use a second device (e.g., **ESP32**) dedicated to BLE scanning, and send data to the Pico via MQTT.

---

## 8. Current Status
*   **Solid Foundation:** The Python script on the Pico handles multitasking and logic merging.
*   **Hardware Agnostic:** The system is no longer tied to a specific project; it can adapt to any Grove-based setup simply by telling the AI what is connected where.
*   **Stable MQTT:** Live updates work without latency.
*   **Reliable AI:** The Assistant now understands the physical limitations of the hardware and the logical hierarchy of the engine.

--- 

## 9. Experimental Interaction Tests
To validate the flexibility and robustness of the Logic Engine, I conducted a series of interaction tests combining different sensors and actuators.
These tests progressively increased in complexity, moving from simple one-to-one behaviors to multi-device reactive systems.

**Basic Sensor → Actuator Tests**
These first experiments validated the core communication pipeline between the AI, MQTT, JSON logic generation, and the Pico runtime.
*   **Distance → Servo Mapping**
A distance sensor was mapped continuously to a servo angle:
- 100mm → 0
- 400mm+ → 180°
This validated smooth interpolation using the `mappings` system.
*   **Temperature → Piezo Alert**
A piezo buzzer played a tone when temperature values exceeded a threshold and stayed silent otherwise.
This confirmed reliable conditional triggering through `rules`.
*   **Light Sensor → LED Nightlight**
A LED automatically turned bright white in dark environments and switched off in bright conditions.
This experiment revealed the importance of inverted mappings for ambient-light interactions.

**State-Based Color Systems**
These experiments focused on multi-state logic and color transitions.
*   **Distance-Based RGB States**
- `< 100mm` → blinking Red
- `100–300mm` → solid Orange
- `> 300mm` → Green
This validated rule priorities, RGB color handling, blinking behaviors, and threshold-based state transitions.
*   **Touch Toggle System**
Each touch toggled a LED between Red and Off.
This demonstrated persistent state management and event-based interactions.

**Multi-Output Reactive Systems**
The next experiments combined several actuators simultaneously.
*   **Distance Alarm System**
Components: Distance sensor, Two LEDs, Piezo buzzer
Behavior:
- If distance `< 200mm`
    - both LEDs blink Red
    - piezo emits a repeating low-volume beep every 0.2s
- Otherwise everything turns off
This validated synchronized multi-output reactions and timing coordination.
*   **Distance Theremin**
Components: Distance sensor, Piezo, LED
Behavior:
- Distance controls piezo pitch
- Distance simultaneously controls LED brightness
This experiment strongly tested the coexistence of multiple continuous `mappings`.

**Interactive Animations**
These final tests explored more expressive and aesthetic behaviors.
*   **Police Car Animation**
Components: Two LEDs, Touch sensor
Behavior:
- LEDs alternate Red/Blue every 0.5s
- Animation activates only while touching the sensor
This validated: timed alternation, concurrent output updates, and conditional animation triggering.
*   **Ambient Light Mood Lamp**
Components: Two LEDs, Light sensor
Behavior:
- In darkness:
    - one LED slowly fades between Purple and Cyan
- In brightness:
    - animation stops
    - second LED becomes Green
This experiment combined: environmental sensing, smooth color interpolation, animated transitions, and conditional state overrides.

**Key Observations From Testing**
These experiments highlighted several important characteristics of the system:
- The distinction between `rules` and `mappings` is essential for avoiding logical conflicts.
- Multi-output synchronization becomes increasingly complex when combining timed animations with continuous mappings.
- The AI performs significantly better when given explicit behavioral constraints and hardware context.
- Small ambiguities in prompts can lead to major logical errors in generated JSON structures.
- The Logic Engine is flexible enough to support both functional interactions (alarms, indicators) and expressive interactions (animations, ambient behaviors).
"""

with open("report.md", "w", encoding="utf-8") as f:
    f.write(content)
