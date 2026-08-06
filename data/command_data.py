"""
Command Training Data
Contains intent definitions and command training corpus for Jean Max.
"""

# Intent & Task Definitions
INTENT_MAP = {
    0: "GREETING",
    1: "OPEN_APP",
    2: "CLOSE_APP",
    3: "CLOSE_ALL_APPS",
    4: "SYSTEM_STATUS",
    5: "BATTERY_STATUS",
    6: "VOLUME_UP",
    7: "VOLUME_DOWN",
    8: "VOLUME_MUTE",
    9: "TIME_DATE",
    10: "WEATHER",
    11: "SEARCH_WEB",
    12: "INTERRUPT",
    13: "TERMINAL_EXEC",
    14: "PHONE_LOCATION",
    15: "START_TRACKING",
    16: "STOP_TRACKING",
    17: "TRACKING_STATUS",
    18: "UNKNOWN"
}

INTENT_TO_ID = {v: k for k, v in INTENT_MAP.items()}

# Command Training Corpus
TRAINING_CORPUS = [
    # GREETING (0)
    ("hello jean", INTENT_TO_ID["GREETING"]),
    ("hey jean max", INTENT_TO_ID["GREETING"]),
    ("hi there", INTENT_TO_ID["GREETING"]),
    ("who are you", INTENT_TO_ID["GREETING"]),
    ("what is your name", INTENT_TO_ID["GREETING"]),
    ("what's your name", INTENT_TO_ID["GREETING"]),
    ("introduce yourself", INTENT_TO_ID["GREETING"]),
    ("good morning", INTENT_TO_ID["GREETING"]),
    ("good evening", INTENT_TO_ID["GREETING"]),
    ("who made you", INTENT_TO_ID["GREETING"]),

    # OPEN_APP (1)
    ("open chrome", INTENT_TO_ID["OPEN_APP"]),
    ("open google chrome", INTENT_TO_ID["OPEN_APP"]),
    ("open vs code", INTENT_TO_ID["OPEN_APP"]),
    ("launch code", INTENT_TO_ID["OPEN_APP"]),
    ("open spotify", INTENT_TO_ID["OPEN_APP"]),
    ("open firefox", INTENT_TO_ID["OPEN_APP"]),
    ("launch calculator", INTENT_TO_ID["OPEN_APP"]),
    ("open terminal", INTENT_TO_ID["OPEN_APP"]),
    ("start browser", INTENT_TO_ID["OPEN_APP"]),
    ("open settings", INTENT_TO_ID["OPEN_APP"]),
    ("open files", INTENT_TO_ID["OPEN_APP"]),
    ("launch spotify", INTENT_TO_ID["OPEN_APP"]),
    ("open sporty way", INTENT_TO_ID["OPEN_APP"]),

    # CLOSE_APP (2)
    ("close firefox", INTENT_TO_ID["CLOSE_APP"]),
    ("close spotify", INTENT_TO_ID["CLOSE_APP"]),
    ("close chrome", INTENT_TO_ID["CLOSE_APP"]),
    ("close terminal", INTENT_TO_ID["CLOSE_APP"]),
    ("exit vs code", INTENT_TO_ID["CLOSE_APP"]),
    ("quit calculator", INTENT_TO_ID["CLOSE_APP"]),
    ("close browser", INTENT_TO_ID["CLOSE_APP"]),
    ("turn off spotify", INTENT_TO_ID["CLOSE_APP"]),

    # CLOSE_ALL_APPS (3)
    ("close all apps", INTENT_TO_ID["CLOSE_ALL_APPS"]),
    ("close all applications", INTENT_TO_ID["CLOSE_ALL_APPS"]),
    ("close everything", INTENT_TO_ID["CLOSE_ALL_APPS"]),
    ("exit all apps", INTENT_TO_ID["CLOSE_ALL_APPS"]),
    ("kill all running applications", INTENT_TO_ID["CLOSE_ALL_APPS"]),

    # SYSTEM_STATUS (4)
    ("system status", INTENT_TO_ID["SYSTEM_STATUS"]),
    ("give me system status", INTENT_TO_ID["SYSTEM_STATUS"]),
    ("what is the system status", INTENT_TO_ID["SYSTEM_STATUS"]),
    ("cpu usage", INTENT_TO_ID["SYSTEM_STATUS"]),
    ("ram usage", INTENT_TO_ID["SYSTEM_STATUS"]),
    ("how is the computer doing", INTENT_TO_ID["SYSTEM_STATUS"]),
    ("check system performance", INTENT_TO_ID["SYSTEM_STATUS"]),

    # BATTERY_STATUS (5)
    ("battery status", INTENT_TO_ID["BATTERY_STATUS"]),
    ("give me battery status", INTENT_TO_ID["BATTERY_STATUS"]),
    ("how much battery left", INTENT_TO_ID["BATTERY_STATUS"]),
    ("check battery", INTENT_TO_ID["BATTERY_STATUS"]),
    ("battery percentage", INTENT_TO_ID["BATTERY_STATUS"]),
    ("is laptop charging", INTENT_TO_ID["BATTERY_STATUS"]),

    # VOLUME_UP (6)
    ("volume up", INTENT_TO_ID["VOLUME_UP"]),
    ("please volume up", INTENT_TO_ID["VOLUME_UP"]),
    ("increase volume", INTENT_TO_ID["VOLUME_UP"]),
    ("make it louder", INTENT_TO_ID["VOLUME_UP"]),
    ("raise volume", INTENT_TO_ID["VOLUME_UP"]),

    # VOLUME_DOWN (7)
    ("volume down", INTENT_TO_ID["VOLUME_DOWN"]),
    ("please volume down", INTENT_TO_ID["VOLUME_DOWN"]),
    ("decrease volume", INTENT_TO_ID["VOLUME_DOWN"]),
    ("make it quieter", INTENT_TO_ID["VOLUME_DOWN"]),
    ("lower volume", INTENT_TO_ID["VOLUME_DOWN"]),
    ("please volume all you more down", INTENT_TO_ID["VOLUME_DOWN"]),
    ("please volume more down", INTENT_TO_ID["VOLUME_DOWN"]),

    # VOLUME_MUTE (8)
    ("mute", INTENT_TO_ID["VOLUME_MUTE"]),
    ("unmute", INTENT_TO_ID["VOLUME_MUTE"]),
    ("mute volume", INTENT_TO_ID["VOLUME_MUTE"]),
    ("mute audio", INTENT_TO_ID["VOLUME_MUTE"]),
    ("silent mode", INTENT_TO_ID["VOLUME_MUTE"]),
    ("please volume silent", INTENT_TO_ID["VOLUME_MUTE"]),

    # TIME_DATE (9)
    ("what time is it", INTENT_TO_ID["TIME_DATE"]),
    ("current time", INTENT_TO_ID["TIME_DATE"]),
    ("what is the date", INTENT_TO_ID["TIME_DATE"]),
    ("today's date", INTENT_TO_ID["TIME_DATE"]),
    ("tell me the time", INTENT_TO_ID["TIME_DATE"]),

    # WEATHER (10)
    ("weather", INTENT_TO_ID["WEATHER"]),
    ("what is the weather", INTENT_TO_ID["WEATHER"]),
    ("weather in delhi", INTENT_TO_ID["WEATHER"]),
    ("weather update", INTENT_TO_ID["WEATHER"]),
    ("how is the weather outside", INTENT_TO_ID["WEATHER"]),

    # SEARCH_WEB (11)
    ("search google for github", INTENT_TO_ID["SEARCH_WEB"]),
    ("search youtube for python tutorials", INTENT_TO_ID["SEARCH_WEB"]),
    ("search for me github.com", INTENT_TO_ID["SEARCH_WEB"]),
    ("search gtapp.com", INTENT_TO_ID["SEARCH_WEB"]),
    ("search web for news", INTENT_TO_ID["SEARCH_WEB"]),
    ("google search artificial intelligence", INTENT_TO_ID["SEARCH_WEB"]),

    # INTERRUPT (12)
    ("wait jean", INTENT_TO_ID["INTERRUPT"]),
    ("stop jean", INTENT_TO_ID["INTERRUPT"]),
    ("pause jean", INTENT_TO_ID["INTERRUPT"]),
    ("shut up jean", INTENT_TO_ID["INTERRUPT"]),

    # TERMINAL_EXEC (13)
    ("update system", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("update the system", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("upgrade system", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("update linux", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("upgrade packages", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("run command", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("execute command", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("terminal update", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("install package", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("clean system", INTENT_TO_ID["TERMINAL_EXEC"]),
    ("check disk space", INTENT_TO_ID["TERMINAL_EXEC"]),

    # PHONE_LOCATION (14)
    ("where is my phone", INTENT_TO_ID["PHONE_LOCATION"]),
    ("phone location", INTENT_TO_ID["PHONE_LOCATION"]),
    ("find my phone", INTENT_TO_ID["PHONE_LOCATION"]),
    ("locate my phone", INTENT_TO_ID["PHONE_LOCATION"]),
    ("phone kidhar hai", INTENT_TO_ID["PHONE_LOCATION"]),
    ("mera phone kidhar hai", INTENT_TO_ID["PHONE_LOCATION"]),
    ("phone kahan hai", INTENT_TO_ID["PHONE_LOCATION"]),
    ("phone location batao", INTENT_TO_ID["PHONE_LOCATION"]),
    ("current phone location", INTENT_TO_ID["PHONE_LOCATION"]),
    ("phone ka location", INTENT_TO_ID["PHONE_LOCATION"]),
    ("phone track karo", INTENT_TO_ID["PHONE_LOCATION"]),
    ("phone location check karo", INTENT_TO_ID["PHONE_LOCATION"]),
    ("get phone location", INTENT_TO_ID["PHONE_LOCATION"]),
    ("what is my phone location", INTENT_TO_ID["PHONE_LOCATION"]),
    ("show me my phone location", INTENT_TO_ID["PHONE_LOCATION"]),

    # START_TRACKING (15)
    ("start tracking", INTENT_TO_ID["START_TRACKING"]),
    ("start phone tracking", INTENT_TO_ID["START_TRACKING"]),
    ("enable tracking", INTENT_TO_ID["START_TRACKING"]),
    ("activate tracking", INTENT_TO_ID["START_TRACKING"]),
    ("phone tracking start karo", INTENT_TO_ID["START_TRACKING"]),
    ("tracking shuru karo", INTENT_TO_ID["START_TRACKING"]),
    ("track my phone", INTENT_TO_ID["START_TRACKING"]),
    ("phone ko track karo", INTENT_TO_ID["START_TRACKING"]),
    ("location tracking start", INTENT_TO_ID["START_TRACKING"]),
    ("monitor my phone", INTENT_TO_ID["START_TRACKING"]),
    ("phone lost", INTENT_TO_ID["START_TRACKING"]),
    ("mera phone gayab hai", INTENT_TO_ID["START_TRACKING"]),
    ("phone kho gaya", INTENT_TO_ID["START_TRACKING"]),
    ("find my phone continuously", INTENT_TO_ID["START_TRACKING"]),
    ("start continuous tracking", INTENT_TO_ID["START_TRACKING"]),

    # STOP_TRACKING (16)
    ("stop tracking", INTENT_TO_ID["STOP_TRACKING"]),
    ("stop phone tracking", INTENT_TO_ID["STOP_TRACKING"]),
    ("disable tracking", INTENT_TO_ID["STOP_TRACKING"]),
    ("deactivate tracking", INTENT_TO_ID["STOP_TRACKING"]),
    ("phone tracking stop karo", INTENT_TO_ID["STOP_TRACKING"]),
    ("tracking band karo", INTENT_TO_ID["STOP_TRACKING"]),
    ("stop monitoring", INTENT_TO_ID["STOP_TRACKING"]),
    ("phone tracking ruk jao", INTENT_TO_ID["STOP_TRACKING"]),
    ("location tracking stop", INTENT_TO_ID["STOP_TRACKING"]),
    ("end phone tracking", INTENT_TO_ID["STOP_TRACKING"]),
    ("cancel tracking", INTENT_TO_ID["STOP_TRACKING"]),

    # TRACKING_STATUS (17)
    ("tracking status", INTENT_TO_ID["TRACKING_STATUS"]),
    ("phone tracking status", INTENT_TO_ID["TRACKING_STATUS"]),
    ("tracking information", INTENT_TO_ID["TRACKING_STATUS"]),
    ("tracking kaisa chal raha hai", INTENT_TO_ID["TRACKING_STATUS"]),
    ("tracking status batao", INTENT_TO_ID["TRACKING_STATUS"]),
    ("monitoring status", INTENT_TO_ID["TRACKING_STATUS"]),
    ("is tracking active", INTENT_TO_ID["TRACKING_STATUS"]),
    ("check tracking status", INTENT_TO_ID["TRACKING_STATUS"]),
    ("phone monitoring status", INTENT_TO_ID["TRACKING_STATUS"]),

    # UNKNOWN (18)
    ("random noise phrase", INTENT_TO_ID["UNKNOWN"]),
    ("something weird", INTENT_TO_ID["UNKNOWN"]),
    ("abracadabra", INTENT_TO_ID["UNKNOWN"])
]
