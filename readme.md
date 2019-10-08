# Triton Monitoring App

Monitoring/Log Viewing Browser app for Oxford Instruments Triton (and probabply newer Kelvinox) Fridges.
Works sowly on the log file, no tempering with the fridge control software required.

# Screenshot
![Screenshot of the app](https://github.com/reneotten/tritonMonitor/blob/master/doc/images/FridgeMonitor.PNG "Screenshot")

# Usage
```
python app.py --filename triton200.json --port 1234
```
`triton200.json` contains all Titles and channel names that vary from system to system and needs to be adopted. Two examples for two of our systems are included. Feel free to add more!



