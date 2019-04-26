#!env python3

import urllib.request as urlrequest
import urllib
import json
import sys


class EDSMNoValuables(Exception):
    pass


oldstate = {}
try:
    statefile = open(".elite.state", 'r+')
    oldstate = json.loads(statefile.read())
    statefile.close()
except Exception:
    pass

state = {}

data = urlrequest.urlopen("http://www.edsm.net/api-logs-v1/get-position?commanderName=Cyphermox&apiKey=40ab52589114886f5baa6f2cd0957c088d85769b")
position = json.loads(data.read())
#print (position)

state['system'] = position.get('system')
#print (state['system'])

try:
    data = urlrequest.urlopen("http://www.edsm.net/api-system-v1/estimated-value?systemName=%s" % state['system'])
    system_value = json.loads(data.read())

    valuables = system_value.get('valuableBodies')
    state['valuables'] = len(valuables)

    if (oldstate.get('system') == state['system'] and oldstate.get('valuables') == state['valuables']):
        raise EDSMNoValuables

    data = urlrequest.urlopen("http://www.edsm.net/api-system-v1/bodies?systemName=%s" % state['system'])
    bodies = json.loads(data.read())

    state['id'] = bodies.get('id64')
    state['bodies'] = bodies.get('bodies')
    state['main_star'] = state['bodies'][0]

    bodies = {}
    state['other_scoopable'] = False
    for body in state['bodies']:
        #print(body)
        bodies[body.get('id')] = {
            'name': body.get('name').replace(state['system'], "").lstrip().replace(" ", ""),
            'type': body.get('subType'),
            'terraform': True if body.get('terraformingState', 'Not terraformable') != 'Not terraformable' else False,
            'volcanism': True if body.get('volcanismType', 'No volcanism') != 'No volcanism' else False,
            'landable': body.get('isLandable', False),
        } 
        if body.get('isMainStar'):
            continue
        if body.get('isScoopable'):
            state['other_scoopable'] = True

    msg = "%s: %s%s%s%s" % (state['system'],
                        #state['main_star'].get('subType').split(' Star')[0],
                        state['main_star'].get('spectralClass'),
                        " " if state['main_star'].get('isScoopable') else "",
                        "+" if state['other_scoopable'] else "",
                        "★" if position.get('firstDiscover') else "")
    for body in valuables:
        #bn = body.get('bodyName')
        #bn = bn.replace(state['system'], "").lstrip()
        bd = bodies[body.get('bodyId')]

        shortType = ""
        if bd['type'] == 'High metal content world':
            shortType = "HMC"
        if bd['type'] == 'Ammonia world':
            shortType = "AW"
        if bd['type'] == 'Rocky body':
            shortType = "RB"

        interest = ""
        if (bd['terraform']):
            interest += "☣ "
        if (bd['volcanism']):
            interest += "☿ "
        if (bd['landable']):
            interest += "☇ "
        msg += (" | %s(%s)%s: %dsl / %dcr" % (bd['name'],
                                                 shortType,
                                                 interest,
                                                 body.get('distance'),
                                                 body.get('valueMax')))

    if state['valuables'] == 0:
        msg += (" | unknown (not scanned or no bodies of value)")

    print(msg)

except urllib.error.HTTPError:
    print("%s: <lookup error>" % (state['system']))

except EDSMNoValuables:
    pass


# clean up before saving state
state['bodies'] = {}
state['main_star'] = {}
with open('.elite.state', 'w') as f:
    print(json.dumps(state), file=f)

