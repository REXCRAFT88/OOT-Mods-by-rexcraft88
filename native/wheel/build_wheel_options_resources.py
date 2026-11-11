"""Add the standalone wheel bumper setting to GameData and System Options.

Run after the standalone wheel candidate exists. The optional --root argument
selects that candidate directory; default is work/wheel-standalone-trial.
"""
import json
import pathlib
import struct
import sys
import zlib

sys.path[:0] = ['work', 'work/jungle', 'outputs/OOT-Test-Kit']
import oot_assets as assets
from byml_inspect import parse
from jungle.lms.common import MessageFile
from jungle.sead.sarc import SARCFile

assets.init()
root = pathlib.Path(sys.argv[sys.argv.index('--root') + 1]) if '--root' in sys.argv else pathlib.Path('work/wheel-standalone-trial')
changes = {}

FIELD = 0xd9749f3e
# This hidden OptionType is accepted by the native menu row factory; map it
# to the independent enum below through the UserSettings descriptor.
OPTION_TYPE = 0x916ac217
# Reuse native ChoiceType values (Hold, Switch, Normal) so the stock option
# widget can serialize/display the three custom labels without a new enum.
RIGHT = 1627154745
LEFT = 556646631
BOTH = 957022509
# The binary On/Off widget ignores ChoiceType and uses generic labels.
# Match the multi-choice widget used by targeting and camera speed instead.
BUTTON = 3569415379


def raw(rel):
    return assets.decompress(assets.read('package1/romfs/' + rel))


def sarc_change(blob, name, member):
    sarc = SARCFile()
    sarc.parse(blob)
    sarc.files[name] = member
    result = sarc.save()
    check = SARCFile()
    check.parse(result)
    assert check.files[name] == member
    return result


def append_dict(blob, fields, endian):
    keyoff = struct.unpack_from(endian + 'I', blob, 4)[0]
    count = int.from_bytes(blob[keyoff + 1:keyoff + 4], 'little' if endian == '<' else 'big')
    keys = []
    for i in range(count):
        pos = keyoff + struct.unpack_from(endian + 'I', blob, keyoff + 4 + i * 4)[0]
        keys.append(blob[pos:blob.index(0, pos)].decode())
    blob.extend(b'\0' * (-len(blob) % 4))
    offset = len(blob)
    blob.extend(b'\xc1' + len(fields).to_bytes(3, 'little' if endian == '<' else 'big'))
    for key, (typ, value) in sorted(fields.items(), key=lambda item: keys.index(item[0])):
        blob.extend(keys.index(key).to_bytes(3, 'little' if endian == '<' else 'big'))
        blob.append(typ)
        blob.extend(struct.pack(endian + 'I', value))
    return offset


def append_array(blob, values, types, endian):
    blob.extend(b'\0' * (-len(blob) % 4))
    offset = len(blob)
    blob.extend(b'\xc0' + len(values).to_bytes(3, 'little' if endian == '<' else 'big'))
    blob.extend(bytes(types))
    blob.extend(b'\0' * (-len(blob) % 4))
    blob.extend(struct.pack(endian + 'I' * len(values), *values))
    return offset


def append_value_string(blob, value, endian):
    table = struct.unpack_from(endian + 'I', blob, 8)[0]
    if table:
        count = int.from_bytes(blob[table + 1:table + 4], 'little' if endian == '<' else 'big')
        strings = []
        for i in range(count):
            pos = table + struct.unpack_from(endian + 'I', blob, table + 4 + i * 4)[0]
            strings.append(blob[pos:blob.index(0, pos)].decode())
        if value in strings:
            return strings.index(value)
    else:
        count = 0
        strings = []
    entries = strings + [value]
    blob.extend(b'\0' * (-len(blob) % 4))
    offset = len(blob)
    blob.extend(b'\xc2' + len(entries).to_bytes(3, 'little' if endian == '<' else 'big'))
    data_start = 4 + len(entries) * 4
    cursor = data_start
    for entry in entries:
        blob.extend(struct.pack(endian + 'I', cursor))
        cursor += len(entry.encode('utf-8')) + 1
    for entry in entries:
        blob.extend(entry.encode('utf-8') + b'\0')
    struct.pack_into(endian + 'I', blob, 8, offset)
    return len(entries) - 1


# OptionSet row: append the three standard shoulder choices next to targeting.
pack_rel = 'Pack/Bootup.Nin_Ounce_NVN2.pack.zs'
original = raw(pack_rel)
members = assets.sarc(original)
option_name = 'UI/OptionSetTable/OptionSetTable.game__ui__OptionSetTable.bgyml'
blob = bytearray(members[option_name])
data, loc, endian = parse(blob)
assert not any(row.get('OptionType') == OPTION_TYPE for row in data['OptionSetArray'])
rows = data['OptionSetArray']
row_ptrs = [struct.unpack_from(endian + 'I', blob, loc[('OptionSetArray', i)][1])[0] for i in range(len(rows))]
choices = append_array(blob, [RIGHT, LEFT, BOTH], [0xd3] * 3, endian)
new_row = append_dict(blob, {
    'ButtonType': (0xd3, BUTTON),
    'ChoiceType': (0xc0, choices),
    'OptionType': (0xd3, OPTION_TYPE),
}, endian)
row_ptrs.insert(8, new_row)
row_array = append_array(blob, row_ptrs, [0xc1] * len(row_ptrs), endian)
struct.pack_into(endian + 'I', blob, loc[('OptionSetArray',)][1], row_array)
verified = parse(blob)[0]
wheel_row = next(row for row in verified['OptionSetArray'] if row.get('OptionType') == OPTION_TYPE)
assert wheel_row['ChoiceType'] == [RIGHT, LEFT, BOTH]
assert wheel_row['ButtonType'] == 0xd4c0f4d3
assert len(verified['OptionSetArray']) == len(rows) + 1
changes[pack_rel] = sarc_change(original, option_name, bytes(blob))

# Independent saved enum setting; its new-account default is Right.
gamedata_rel = 'GameData/GameDataList.Product.110.byml.zs'
blob = bytearray(raw(gamedata_rel))
data, loc, endian = parse(blob)
assert not any(row['Hash'] == FIELD for row in data['Data']['Enum'])
right_index = append_value_string(blob, 'Hold', endian)
left_index = append_value_string(blob, 'Switch', endian)
both_index = append_value_string(blob, 'Normal', endian)
raw_values = append_array(blob, [right_index, left_index, both_index], [0xa0] * 3, endian)
# BYML UInt64 (0xd5) stores an offset to an eight-byte payload, not a
# string-table index. Invalid payloads display correctly via RawValues but
# make GameData reject every selected value as outside the enum's domain.
value_offsets = []
for token in [RIGHT, LEFT, BOTH]:
    blob.extend(b'\0' * (-len(blob) % 8))
    value_offsets.append(len(blob))
    blob.extend(struct.pack(endian + 'Q', token))
enum_values = append_array(blob, value_offsets, [0xd5] * 3, endian)
new_enum = append_dict(blob, {
    'DefaultValue': (0xd3, RIGHT),
    'Hash': (0xd3, FIELD),
    'RawValues': (0xc0, raw_values),
    'ResetTypeValue': (0xd1, 4),
    'SaveFileIndex': (0xd1, 1),
    'Values': (0xc0, enum_values),
}, endian)
enum_ptrs = [struct.unpack_from(endian + 'I', blob, loc[('Data', 'Enum', i)][1])[0] for i in range(len(data['Data']['Enum']))]
enum_ptrs.append(new_enum)
enum_array = append_array(blob, enum_ptrs, [0xc1] * len(enum_ptrs), endian)
struct.pack_into(endian + 'I', blob, loc[('Data', 'Enum')][1], enum_array)

# Include the saved field in the account settings descriptor's default map.
descriptor_index = next(i for i, row in enumerate(data['Data']['Struct']) if row['Hash'] == 0x834d9d9e)
descriptor = data['Data']['Struct'][descriptor_index]['DefaultValue']
assert not any(row['Hash'] == FIELD for row in descriptor)
new_default = append_dict(blob, {'Hash': (0xd3, OPTION_TYPE), 'Value': (0xd3, FIELD)}, endian)
default_ptrs = [struct.unpack_from(endian + 'I', blob, loc[('Data', 'Struct', descriptor_index, 'DefaultValue', i)][1])[0] for i in range(len(descriptor))]
default_ptrs.append(new_default)
default_array = append_array(blob, default_ptrs, [0xc1] * len(default_ptrs), endian)
struct.pack_into(endian + 'I', blob, loc[('Data', 'Struct', descriptor_index, 'DefaultValue')][1], default_array)

for key, delta in [('AllDataSaveOffset', 8), ('AllDataSaveSize', 64)]:
    struct.pack_into(endian + 'I', blob, loc[('MetaData', key)][1], data['MetaData'][key] + delta)
for key, delta in [('SaveDataOffsetPos', 8), ('SaveDataSize', 64)]:
    struct.pack_into(endian + 'I', blob, loc[('MetaData', key, 1)][1], data['MetaData'][key][1] + delta)
verified = parse(blob)[0]
new = next(row for row in verified['Data']['Enum'] if row['Hash'] == FIELD)
assert new['DefaultValue'] == RIGHT and new['RawValues'] == ['Hold', 'Switch', 'Normal']
assert [struct.unpack_from(endian + 'Q', blob, value['raw'])[0]
        for value in new['Values']] == [RIGHT, LEFT, BOTH]
assert any(row['Hash'] == OPTION_TYPE and row['Value'] == FIELD
           for row in verified['Data']['Struct'][descriptor_index]['DefaultValue'])
changes[gamedata_rel] = bytes(blob)

# Add translated menu strings to every installed language pack, matching the
# existing standalone wheel's English fallback convention.
languages = [item['path'].removeprefix('package1/romfs/') for item in assets.INDEX
             if item['path'].startswith('package1/romfs/Mals/') and item['path'].endswith('.sarc.zs')]
labels = {
    'MessageWindowTransparency_Title': 'Wheel Bumper',
    'MessageWindowTransparency_Caption': 'Choose which bumper opens the item wheel.',
    'MessageWindowTransparency_00': 'Right',
    'MessageWindowTransparency_01': 'Left',
    'MessageWindowTransparency_02': 'Both',
}
for rel in languages:
    original = raw(rel)
    members = assets.sarc(original)
    name = 'LayoutMsg/SystemOption_00.msbt'
    message = MessageFile()
    message.parse(members[name])
    table, buckets = message.parse_labels(message.blocks['LBL1'])
    text = message.blocks['TXT2']
    endian = message.endianness
    count = struct.unpack_from(endian + 'I', text)[0]
    offsets = struct.unpack_from(endian + 'I' * count, text, 4)
    strings = [text[offset:offsets[i + 1] if i + 1 < count else len(text)] for i, offset in enumerate(offsets)]
    for key, value in labels.items():
        if key not in table:
            table[key] = len(strings)
            strings.append(b'')
        strings[table[key]] = (value + '\0').encode('utf-8')
    rebuilt = bytearray(struct.pack(endian + 'I', len(strings)))
    offset = 4 + 4 * len(strings)
    for value in strings:
        rebuilt.extend(struct.pack(endian + 'I', offset))
        offset += len(value)
    message.blocks['TXT2'] = bytes(rebuilt) + b''.join(strings)
    message.blocks['LBL1'] = message.save_labels(table, buckets)
    changes[rel] = sarc_change(original, name, message.save())

# Emit changed compressed resources and grow their RSZ allocation entries.
size_rel = 'System/Resource/ResourceSizeTable.Product.111.Nin_Ounce_NVN2.rsizetable.zs'
size_path = root / 'romfs' / size_rel
size_table = bytearray(raw(size_rel))
entries = struct.unpack_from('<I', size_table, 14)[0]
for rel, content in changes.items():
    path = root / 'romfs' / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    packed = assets.zs.ZstdCompressor(level=12, dict_data=assets.DICT[1]).compress(content)
    path.write_bytes(packed)
    assert assets.decompress(path.read_bytes()) == content
    digest = zlib.crc32(rel.removesuffix('.zs').encode())
    hits = [i for i in range(22, 22 + entries * 8, 8) if struct.unpack_from('<I', size_table, i)[0] == digest]
    assert len(hits) == 1, (rel, hits)
    at = hits[0] + 4
    prior = struct.unpack_from('<I', size_table, at)[0]
    growth = max(0, len(content) - len(raw(rel)))
    struct.pack_into('<I', size_table, at, (prior + growth + 65535) & ~65535)

option_hash = zlib.crc32(option_name.encode())
option_at = next(i + 4 for i in range(22, 22 + entries * 8, 8)
                 if struct.unpack_from('<I', size_table, i)[0] == option_hash)
struct.pack_into('<I', size_table, option_at, max(65536, struct.unpack_from('<I', size_table, option_at)[0]))
size_path.parent.mkdir(parents=True, exist_ok=True)
font_at = next(i + 4 for i in range(22, 22 + entries * 8, 8)
               if struct.unpack_from('<I', size_table, i)[0] == 0x8909365f)
struct.pack_into('<I', size_table, font_at, max(16384, struct.unpack_from('<I', size_table, font_at)[0]))
size_path.write_bytes(assets.zs.ZstdCompressor(level=12).compress(size_table))
print(json.dumps({'status': 'resources updated', 'field_hash': hex(FIELD),
                  'choice_hashes': [hex(RIGHT), hex(LEFT), hex(BOTH)],
                  'changed_resources': len(changes), 'root': str(root)}, indent=2))
