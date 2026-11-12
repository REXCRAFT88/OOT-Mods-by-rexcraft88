"""Append-only BYML and SARC edits; preserve original indices and untouched data."""

import struct

from jungle.sead.sarc import SARCFile

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
