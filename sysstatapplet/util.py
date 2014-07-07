def prettyPrintBytesSec(b):
    units = [ "B/s", "kB/s", "MB/s", "GB/s", "TB/s"]
    unit = 0
    while b > 1024:
        b /= 1024.
        unit += 1
    if b > 100:
        b /= 1024.
        unit += 1
    if unit == 0:
        return "%d%s" % (b, units[unit])
    return "%.1f%s" % (b, units[unit])

def getByteScale(s):
    units = { "B": 0, "kB": 1, "MB": 2, "GB": 3, "TB": 4}
    e = units.get(s,0)
    return 1024**e
