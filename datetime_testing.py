from datetime import UTC, datetime

ISO_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
dt = datetime.now(tz=UTC).strftime(ISO_FORMAT)[:-3]
print(dt)
