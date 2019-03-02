import win32evtlog

server = "localhost"
logtype = "System"
hand = win32evtlog.OpenEventLog(server, logtype)
flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
total = win32evtlog.GetNumberOfEventLogRecords(hand)
current = 0
while current < 20:
    events = win32evtlog.ReadEventLog(hand, flags, 0)
    if events:
        for event in events:
            print("Event Category:", event.EventCategory)
            print("Time Generated:", event.TimeGenerated)
            print("Source Name:", event.SourceName)
            print("Event ID:", event.EventID)
            print("Event Type:", event.EventType)
            data = event.StringInserts
            if data:
                print("Event Data:")
                for msg in data:
                    print(msg)
            print
    current += 1
