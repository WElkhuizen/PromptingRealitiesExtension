# Log of progress

## Entry 25-04-2026
WSE: I was succesful in programming logic via the prompting realities interface, using the MQTT and JSON format.
I can make f.i.:
- Make the touch sensor trigger the LED.
- Map the lightsensor value to the brightness of the LED, and also its inverse.

I then added a calibration sequence, so that you can also get a min and max value for the analog inputs, given your context. I got this to work for the light sensor. 

I used the receiver topic (set to receiver/led_control/sensors) in the chat interface, to get data back from the itsybitsy. I has a initial calibration loop of about 25 seconds, where it reads the minimal and maximum values of the light sensor. 

Next I tried to generalise this intruction for all analog inputs (f.i. also for the temperature sensor), but now this calibration sequence seems a bit broken. At least it does not give clear instructions to the user any more on what to do. 

### Giving Claude control of the browser
Claude can also directly edit all the data in the browser via Chrome. I have set it up so that it can copy-paste the prompt instruction and JSON. and that it can type messages in the chat interface. Only gave permission to access and change in the web browser for this one domain. 

### Issues remaining & ideas to try out:
- I also tested creating arrays of values, so that you can for instance make the light blink (without varying the input signal directly). This was not succesful so far. 
- The generalisation of the mapping calibration sequence seems to have broken the clear prompting instructions to the user. This needs to be fixed. 
- Make the LLM talk in less technical terms, and use less of the variable names etc. from the MQTT string. 
- Find some way to (automatically)describe the physical configuration that is created by the user. The user might also need instructions on how to assemble the components. 
- Can I provide claude with better info about the breakout board. I sometimes suggest connecting to ports that are not available. 
- Test other forms of logic, and possibly also combining logic: e.g. mapping + boolean operations. 
I seemed to have also created an (partial) example where both the brightness of the light could be influenced by the light sensor, and the color could be influenced by the touch sensor. however, if the touch sensor was pressed the mapping function no longer seemed to work. 
- I also tried to use an array to make the LED cyle over RED, BLUE and GREEN, but the cycle still seems too fast. I do see the different values in the mu editor, but i cannot distinguish them visually. if i ask it to go even slower, it just shows the red color. no real cycle any more. the timing part probably needs a bit more work in the circuitpython code.
