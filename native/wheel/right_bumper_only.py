"""Disable only the native left-bumper shortcut branches, not controller input.

Build-time dependency: ainb. Run from the development workspace after building
the compatibility candidate. Public installers apply hash-checked binary deltas.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, 'outputs/OOT-Test-Kit')
import ainb
from nup_overlay import Nup

source = Nup(json.load(open('outputs/OOT-Test-Kit/settings.json'))['source_nup'])
package = source.best_package()['index']
root = Path(sys.argv[sys.argv.index('--root') + 1]) if '--root' in sys.argv else Path('work/compatibility-candidates/item-wheel')
for name, selectors, query in [
    ('Event', [141], 35),
    ('ShortCut', [52], 3),
    ('UpdateShortCutOpenHoldFrameCounter', [3, 14], None),
]:
    path = 'romfs/Sequence/' + name + '.module.ainb'
    original = source.read(package, path)
    document = ainb.AINB.from_binary(original).as_dict()
    for index in selectors:
        node = document['Nodes'][index]
        parameter = node['Parameters']['Inputs']['Bool'][0]
        assert parameter['Output Index'] == 3  # HoldL / TrigL
        if query is not None:
            assert parameter['Node Index'] == query
        outputs = document['Nodes'][parameter['Node Index']]['Parameters']['Outputs']['Bool']
        assert outputs[3]['Name'] in ('HoldL', 'TrigL')
        children = node['Plugs']['Child']
        false = next(c['Node Index'] for c in children if c['Name'] == 'False')
        next(c for c in children if c['Name'] == 'True')['Node Index'] = false
    result = ainb.AINB.from_dict(document)
    if result.blackboard is None:
        result.blackboard = ainb.Blackboard()
    binary = result.to_binary()
    assert len(binary) <= len(original), 'Do not increase resource allocation'
    assert ainb.AINB.from_binary(binary).as_dict() == document
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(binary)
    print(name, 'left shortcut disabled; resource allocation not increased')

