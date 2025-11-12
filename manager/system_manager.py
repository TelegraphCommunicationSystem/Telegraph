

SYSTEMDATA = "config/SYSTEMDATA.DAT"

def read_systemdata():
    with open(SYSTEMDATA) as f:
        lines = f.readlines()
    data = {}
    for line in lines:
        id, totp_secret = line.strip("\n").split(";")
        data['ID'] = id
        data['TS'] = totp_secret
    return data