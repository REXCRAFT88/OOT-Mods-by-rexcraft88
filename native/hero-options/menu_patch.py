"""Build a bounded native OptionType extension patch plan for the OOT menu.

The linked private module supplies the three hook/data symbols. This module
only patches the known main-text call sites and keeps every edit guarded by
the original instruction bytes. The game image is not modified by importing
this file; call build_plan/apply_plan from the private candidate builder.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct

import mmh3


ENUMS = (
    (18, "HeroStamina"),
    (19, "HeroStaminaAmount"),
    (20, "HeroManualShield"),
    (21, "HeroItemWheel"),
    (22, "HeroWheelBumper"),
    (23, "HeroDifficulty"),
    (24, "HeroNoRecoveryDrops"),
)
STOCK_HASH_COUNT = 18
MAX_OPTION_TYPE = 24
ENUM_HASH_TABLE = 0x3F13750
ENUM_SORTED_PERMUTATION = 0x3F13798
ENUM_NAMES_BASE = 0x3F137E0
BYML_OPTION_TYPE_READER = 0x339AB40
HASH_TO_ENUM_ID = 0x339AF00
NAME_LOOKUP_PAIRS = (
    (0x339C2F8, 0x339C2FC), # Runtime field hash initialization uses a GOT load.
    (0x339AD7C, 0x339AD80),
    (0x33CF604, 0x33CF608),
    (0x33CF824, 0x33CF828),
    (0x33CFFBC, 0x33CFFC0),
    (0x34032AC, 0x34032B0),
    (0x340397C, 0x3403980),
    (0x3403A18, 0x3403A1C),
)


def mmh3_u32(text: str) -> int:
    return mmh3.hash(text, signed=False)


def enum_hashes() -> tuple[int, ...]:
    return tuple(mmh3_u32(name) for _, name in ENUMS)


def make_private_enum_tables(main_text: bytes) -> tuple[bytes, bytes, bytes]:
    """Copy stock metadata and append the seven new names in private storage.

    The native lookup order is the hash array plus a u32 permutation sorted by
    hash. Names use a string blob followed at +0x144 by signed 32-bit offsets
    relative to the blob base. The returned blobs are hashes, permutation, and
    names, respectively, for placement in module .rodata.
    """
    def u32(at: int) -> int:
        return struct.unpack_from("<I", main_text, at)[0]

    stock_hashes = [u32(ENUM_HASH_TABLE + 4 * i) for i in range(STOCK_HASH_COUNT)]
    if len(set(stock_hashes)) != STOCK_HASH_COUNT:
        raise ValueError("stock enum hash table contains duplicates")
    hashes = stock_hashes + list(enum_hashes())
    if len(set(hashes)) != len(hashes):
        raise ValueError("custom enum hash collides with a stock/custom hash")
    hashes_blob = struct.pack("<25I", *hashes)
    permutation_blob = struct.pack("<25I", *sorted(range(25), key=hashes.__getitem__))

    old_offsets = [struct.unpack_from("<i", main_text, ENUM_NAMES_BASE + 0x144 + 4 * i)[0]
                   for i in range(STOCK_HASH_COUNT)]
    names = []
    for relative in old_offsets:
        start = ENUM_NAMES_BASE + relative
        if not 0 <= start < len(main_text):
            raise ValueError(f"stock enum name offset out of range: {relative}")
        end = main_text.find(b"\0", start)
        if end < 0:
            raise ValueError(f"unterminated stock enum name at {start:#x}")
        names.append(main_text[start:end + 1])
    names.extend(name.encode("ascii") + b"\0" for _, name in ENUMS)
    name_blob = bytearray(main_text[ENUM_NAMES_BASE:ENUM_NAMES_BASE + 0x144])
    name_blob.extend(b'\0' * (25 * 4))
    for i, relative in enumerate(old_offsets):
        struct.pack_into('<i', name_blob, 0x144 + i * 4, relative)
        assert name_blob[relative:relative+len(names[i])] == names[i]
    for i, value in enumerate(names[18:], 18):
        struct.pack_into('<i', name_blob, 0x144 + i * 4, len(name_blob))
        name_blob.extend(value)
    return hashes_blob, permutation_blob, bytes(name_blob)


def emit_module_data_assembly(main_text: bytes) -> str:
    """Render the generated private tables as assembler data for the module."""
    hashes, permutation, names = make_private_enum_tables(main_text)
    sections = (
        ("hero_menu_option_hashes", hashes),
        ("hero_menu_option_sorted_indices", permutation),
        ("hero_menu_option_names", names),
    )
    out = [".section .rodata.hero_menu,\"a\",%progbits", ".balign 8"]
    for symbol, data in sections:
        out.extend((f".global {symbol}", f".type {symbol}, %object", f"{symbol}:"))
        for start in range(0, len(data), 16):
            out.append("  .byte " + ", ".join(f"0x{b:02x}" for b in data[start:start + 16]))
        out.extend((f".size {symbol}, .-{symbol}", ".balign 8"))
    return "\n".join(out) + "\n"


def a64_branch(source: int, target: int) -> bytes:
    delta = target - source
    if delta & 3 or not -(1 << 27) <= delta < (1 << 27):
        raise ValueError(f"A64 B target out of range/alignment: {source:#x}->{target:#x}")
    return struct.pack("<I", 0x14000000 | ((delta >> 2) & 0x03FFFFFF))


def encode_adrp(rd: int, pc: int, target: int) -> int:
    """Encode ADRP Xrd, target using page-relative addressing."""
    pages = (target >> 12) - (pc >> 12)
    if not -(1 << 20) <= pages < (1 << 20):
        raise ValueError(f"ADRP target out of range: {pc:#x}->{target:#x}")
    imm = pages & 0x1FFFFF
    return 0x90000000 | ((imm & 3) << 29) | (((imm >> 2) & 0x7FFFF) << 5) | rd


def encode_add_imm(rd: int, rn: int, imm12: int) -> int:
    if not 0 <= imm12 <= 0xFFF:
        raise ValueError("ADD immediate must fit 12 bits")
    return 0x91000000 | (imm12 << 10) | (rn << 5) | rd


def encode_adrp_add_pair(adrp_pc: int, adrp_rd: int, add_rd: int,
                         add_rn: int, target: int) -> tuple[bytes, bytes]:
    hi = encode_adrp(adrp_rd, adrp_pc, target)
    lo = encode_add_imm(add_rd, add_rn, target & 0xFFF)
    return struct.pack("<I", hi), struct.pack("<I", lo)


@dataclass(frozen=True)
class Patch:
    address: int
    expected: bytes
    replacement: bytes
    reason: str


def build_plan(main_text: bytes, symbols: dict[str, int]) -> list[Patch]:
    """Return guarded patches; symbols are addresses in the loaded main image.

    Requires Capstone to locate each inlined enum bounds check in its local
    basic-block prefix. This makes compiler layout changes fail closed.
    """
    try:
        from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
        from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_REG, ARM64_OP_MEM
    except ImportError as exc:
        raise RuntimeError("Capstone is required to locate native enum bounds checks") from exc

    required = ("hero_menu_hash_to_enum_id", "hero_menu_byml_option_type_reader",
                "hero_menu_option_names")
    missing = [name for name in required if name not in symbols]
    if missing:
        raise KeyError("missing linked module symbols: " + ", ".join(missing))

    def word(at: int) -> int:
        if at < 0 or at + 4 > len(main_text):
            raise ValueError(f"main-text lacks instruction at {at:#x}")
        return struct.unpack_from("<I", main_text, at)[0]

    patches: list[Patch] = [
        Patch(HASH_TO_ENUM_ID, main_text[HASH_TO_ENUM_ID:HASH_TO_ENUM_ID + 4],
              a64_branch(HASH_TO_ENUM_ID, symbols["hero_menu_hash_to_enum_id"]),
              "replace stock hash-to-ID helper with 25-entry lookup"),
        Patch(BYML_OPTION_TYPE_READER,
              main_text[BYML_OPTION_TYPE_READER:BYML_OPTION_TYPE_READER + 4],
              a64_branch(BYML_OPTION_TYPE_READER,
                        symbols["hero_menu_byml_option_type_reader"]),
              "intercept custom BYML OptionType hashes; tail-call stock parser otherwise"),
    ]

    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    for adrp_at, add_at in NAME_LOOKUP_PAIRS:
        adrp_word, add_word = word(adrp_at), word(add_at)
        ins = list(md.disasm(struct.pack("<II", adrp_word, add_word), adrp_at))
        got_pair=adrp_at==0x339c2f8
        if len(ins) != 2 or ins[0].mnemonic != "adrp" or ins[1].mnemonic != ("ldr" if got_pair else "add"):
            raise ValueError(f"expected ADRP/ADD name-base pair at {adrp_at:#x}")
        adrp_ops, add_ops = ins[0].operands, ins[1].operands
        if len(adrp_ops) != 2 or len(add_ops) < (2 if got_pair else 3):
            raise ValueError(f"unexpected name-base operand shape at {adrp_at:#x}")
        rd = adrp_ops[0].reg
        if got_pair:
            valid=add_ops[0].reg==rd and add_ops[1].type==ARM64_OP_MEM and add_ops[1].mem.base==rd and add_ops[1].mem.disp==0x958
        else:
            valid=add_ops[0].reg==rd and add_ops[1].reg==rd and add_ops[2].type==ARM64_OP_IMM
        if not valid:
            raise ValueError(f"name-base pair register mismatch at {adrp_at:#x}")
        # Capstone register IDs are not architectural numbers. Extract Xn from
        # its canonical register name, which is stable across its supported builds.
        regname = md.reg_name(rd)
        if not regname.startswith("x") or not regname[1:].isdigit():
            raise ValueError(f"unexpected ADRP destination {regname!r} at {adrp_at:#x}")
        rn = int(regname[1:])
        new_pair = encode_adrp_add_pair(
            adrp_at, rn, int(md.reg_name(add_ops[0].reg)[1:]),
            rn, symbols["hero_menu_option_names"])
        patches.extend((
            Patch(adrp_at, struct.pack("<I", adrp_word), new_pair[0],
                  "relocate OptionType names table base"),
            Patch(add_at, struct.pack("<I", add_word), new_pair[1],
                  "relocate OptionType names table base"),
        ))

        # The bound check is in the short prefix immediately before the table
        # address is formed. Require one compare against the stock last index.
        start = max(0, adrp_at - 0x80)
        prefix = main_text[start:adrp_at]
        candidates = []
        for insn in md.disasm(prefix, start):
            if insn.mnemonic != "cmp" or len(insn.operands) != 2:
                continue
            left, right = insn.operands
            if left.type == ARM64_OP_REG and right.type == ARM64_OP_IMM and right.imm == 17:
                candidates.append(insn)
        if len(candidates) != 1:
            raise ValueError(f"expected one CMP #17 before name use at {adrp_at:#x}; found {len(candidates)}")
        cmp_insn = candidates[0]
        old = word(cmp_insn.address)
        # CMP immediate is SUBS WZR/XZR, Wn, #imm12; change only imm12.
        replacement = (old & ~(0xFFF << 10)) | (MAX_OPTION_TYPE << 10)
        patches.append(Patch(cmp_insn.address, struct.pack("<I", old),
                             struct.pack("<I", replacement),
                             "extend names lookup bound from 17 to 24"))

    addresses = [p.address for p in patches]
    if len(addresses) != len(set(addresses)):
        raise ValueError("overlapping/duplicate patch addresses")
    return patches


def apply_plan(main_text: bytearray, patches: list[Patch]) -> None:
    """Apply a plan only when all stock bytes still match."""
    for patch in patches:
        actual = bytes(main_text[patch.address:patch.address + len(patch.expected)])
        if actual != patch.expected:
            raise ValueError(f"stock bytes changed at {patch.address:#x}: {actual.hex()} != {patch.expected.hex()}")
    for patch in patches:
        main_text[patch.address:patch.address + len(patch.replacement)] = patch.replacement


def write_plan_json(patches: list[Patch], path: str) -> None:
    import json
    from pathlib import Path
    Path(path).write_text(json.dumps([
        {"address": hex(p.address), "expected": p.expected.hex(),
         "replacement": p.replacement.hex(), "reason": p.reason}
        for p in patches
    ], indent=2) + "\n")
