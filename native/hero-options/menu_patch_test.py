"""Small host-side checks for the bounded native menu extension helpers."""
import struct
import unittest

import menu_patch as menu


class MenuPatchTests(unittest.TestCase):
    def test_ids_hashes_and_stock_nonreuse(self):
        self.assertEqual([i for i, _ in menu.ENUMS], list(range(18, 25)))
        hashes = menu.enum_hashes()
        self.assertEqual(len(set(hashes)), 7)
        self.assertEqual(hashes, tuple(menu.mmh3_u32(name) for _, name in menu.ENUMS))

    def test_private_table_expands_all_three_stock_tables(self):
        text = bytearray(0x4000000)
        stock = [0x1000 + 37 * i for i in range(18)]
        struct.pack_into("<18I", text, menu.ENUM_HASH_TABLE, *stock)
        old_names = [f"StockType{i:02}".encode() + b"\0" for i in range(18)]
        cursor = menu.ENUM_NAMES_BASE
        for i, value in enumerate(old_names):
            struct.pack_into("<i", text, menu.ENUM_NAMES_BASE + 0x144 + i * 4,
                             cursor - menu.ENUM_NAMES_BASE)
            text[cursor:cursor + len(value)] = value
            cursor += len(value)
        hashes_blob, permutation_blob, names_blob = menu.make_private_enum_tables(text)
        hashes = struct.unpack("<25I", hashes_blob)
        permutation = struct.unpack("<25I", permutation_blob)
        self.assertEqual(hashes[:18], tuple(stock))
        self.assertEqual(hashes[18:], menu.enum_hashes())
        self.assertEqual(sorted(permutation), list(range(25)))
        self.assertEqual([hashes[i] for i in permutation], sorted(hashes))
        self.assertGreaterEqual(len(names_blob),0x144+25*4)
        extracted = []
        for i in range(25):
            rel = struct.unpack_from("<i", names_blob, 0x144+i*4)[0]
            end = names_blob.index(0, rel)
            extracted.append(names_blob[rel:end].decode("ascii"))
        self.assertEqual(extracted[:18], [n[:-1].decode() for n in old_names])
        self.assertEqual(extracted[18:], [name for _, name in menu.ENUMS])

    def test_a64_branch_and_name_pair_encodings(self):
        branch = struct.unpack("<I", menu.a64_branch(0x1000, 0x1800))[0]
        self.assertEqual(branch, 0x14000200)
        hi, lo = menu.encode_adrp_add_pair(0x1000, 4, 4, 4, 0x2345)
        self.assertEqual(struct.unpack("<I", hi)[0] & 31, 4)
        self.assertEqual(struct.unpack("<I", lo)[0], menu.encode_add_imm(4, 4, 0x345))

    def test_unknown_hash_fails_closed_in_plan_contract(self):
        self.assertEqual(menu.STOCK_HASH_COUNT, 18)
        self.assertEqual(menu.MAX_OPTION_TYPE, 24)
        self.assertEqual(menu.BYML_OPTION_TYPE_READER, 0x339AB40)
        self.assertEqual(menu.HASH_TO_ENUM_ID, 0x339AF00)
        self.assertEqual(len(menu.NAME_LOOKUP_PAIRS), 8)


if __name__ == "__main__":
    unittest.main()
