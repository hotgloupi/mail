

def parse(data):
    res = []
    for line in data.split('\n'):
        res.append([line.replace('\r', '').strip()])
    return res
