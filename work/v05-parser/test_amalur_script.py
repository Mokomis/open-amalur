"""Safety, structural validation, and fingerprinted real-sample tests."""
import hashlib
import io
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from amalur_script import Limits, ParseError, TYPE_NAMES, main, parse_bytes, parse_file


def be(value):
    return struct.pack(">I",value)


def string(value):
    if value is None:
        return be(0)
    raw = value.encode() + b"\0"
    return be(len(raw)) + raw


def function(words=None, constants=(), children=(), debug=(0,0,0), params=0):
    words = words if words is not None else [0x12020000]
    return (string(None) * 2 + be(0) * 2 + be(0) + be(params) + b"\x02"
            + be(1) + be(len(words)) + b"".join(be(w) for w in words)
            + be(len(constants)) + b"".join(constants) + be(len(children))
            + b"".join(children) + b"".join(be(c) for c in debug))


def chunk(fn=None, trailer=None):
    header = bytes.fromhex("1b4c756151080004040404010100")
    table = be(len(TYPE_NAMES)) + b"".join(be(i)+string(n) for i,n in enumerate(TYPE_NAMES))
    return header + table + (function() if fn is None else fn) + (be(1)+string(None) if trailer is None else trailer)


def wrapper(payload, name=b"fixture", metadata=()):
    strings = b"".join(struct.pack("<I", len(value)) + value for value in metadata)
    return (struct.pack("<I",len(name)) + name + struct.pack("<I",len(metadata))
            + strings + struct.pack("<I",len(payload)) + payload)


class StructuralTests(unittest.TestCase):
    def test_reordered_valid_type_entries_rejected(self):
        entries = [be(i) + string(n) for i, n in enumerate(TYPE_NAMES)]
        entries[0], entries[1] = entries[1], entries[0]
        data = chunk()[:14] + be(len(entries)) + b"".join(entries) + function() + be(1) + string(None)
        with self.assertRaisesRegex(ParseError, "type table order"):
            parse_bytes(data)

    def test_signed_number_constants_preserve_extremes(self):
        values = [-2147483648, -1, 0, 2147483647]
        constants = [b"\x03" + struct.pack(">i", v) for v in values]
        parsed = parse_bytes(chunk(function(constants=constants)))
        found = parsed["chunk"]["root_function"]["constants"]
        self.assertEqual([c["integer_value"] for c in found], values)
        self.assertEqual([c["raw_hex"] for c in found], ["80000000", "ffffffff", "00000000", "7fffffff"])

    def test_minimal_chunk_and_wrapper(self):
        raw = chunk()
        a,b = parse_bytes(raw),parse_bytes(wrapper(raw,metadata=(b"fixture.reference", b"other")))
        self.assertEqual(a["chunk"]["summary"],{"functions":1,"instructions":1,"constants":0})
        self.assertEqual(b["wrapper"]["metadata_string_count"],2)
        self.assertEqual([x["text"] for x in b["wrapper"]["metadata_strings"]], ["fixture.reference", "other"])
        self.assertEqual(b["chunk"]["payload_bytes_consumed"],len(raw))
        self.assertEqual(b["chunk"]["root_function"]["code_file_offset"],a["chunk"]["root_function"]["code_file_offset"]+b["wrapper"]["payload_file_offset"])

    def test_every_truncation_of_minimal_chunk_rejected(self):
        raw = chunk()
        for end in range(len(raw)):
            with self.subTest(end=end),self.assertRaises(ParseError):
                parse_bytes(raw[:end])

    def test_every_truncation_of_wrapper_rejected(self):
        raw = wrapper(chunk())
        for end in range(len(raw)):
            with self.subTest(end=end),self.assertRaises(ParseError):
                parse_bytes(raw[:end])

    def test_metadata_wrapper_truncation_is_not_ignored(self):
        raw = wrapper(chunk(), metadata=(b"one", b"two"))
        for end in range(len(raw)):
            with self.subTest(end=end), self.assertRaises(ParseError):
                parse_bytes(raw[:end])

    def test_metadata_count_bounded(self):
        raw = struct.pack("<I", 1) + b"x" + struct.pack("<I", 4097) + bytes(20000)
        with self.assertRaisesRegex(ParseError, "metadata count"):
            parse_bytes(raw)

    def test_metadata_string_length_bounded(self):
        raw = wrapper(chunk(), metadata=(b"a" * 100,))
        with self.assertRaisesRegex(ParseError, "metadata string length"):
            parse_bytes(raw, Limits(max_string_bytes=32))

    def test_trailing_bytes_not_silently_ignored(self):
        with self.assertRaisesRegex(ParseError,"trailing"):
            parse_bytes(chunk()+b"\0")

    def test_wrapper_length_mismatch(self):
        with self.assertRaisesRegex(ParseError,"payload size"):
            parse_bytes(wrapper(chunk())+b"\0")

    def test_unsupported_format(self):
        data=bytearray(chunk());data[5]=14
        with self.assertRaisesRegex(ParseError,"unsupported header"):
            parse_bytes(bytes(data))

    def test_unsupported_endian(self):
        data=bytearray(chunk());data[6]=1
        with self.assertRaisesRegex(ParseError,"unsupported header"):
            parse_bytes(bytes(data))

    def test_oversized_wrapper_name(self):
        with self.assertRaisesRegex(ParseError,"wrapper name length"):
            parse_bytes(struct.pack("<I",0xffffffff))

    def test_type_count_limit(self):
        data=bytearray(chunk());data[14:18]=be(0xffffffff)
        with self.assertRaisesRegex(ParseError,"type count"):
            parse_bytes(bytes(data))

    def test_instruction_count_limit(self):
        data=bytearray(chunk());data[267:271]=be(0xffffffff)
        with self.assertRaisesRegex(ParseError,"instruction count"):
            parse_bytes(bytes(data))

    def test_bad_constant_type(self):
        with self.assertRaisesRegex(ParseError,"constant type"):
            parse_bytes(chunk(function(constants=[b"\xff"])))

    def test_bad_string_termination(self):
        constant=b"\x04"+be(4)+b"abcd"
        with self.assertRaisesRegex(ParseError,"terminating NUL"):
            parse_bytes(chunk(function(constants=[constant])))

    def test_opcode_outside_table(self):
        with self.assertRaisesRegex(ParseError,"opcode"):
            parse_bytes(chunk(function(words=[0xff000000])))

    def test_constant_index_outside_array(self):
        with self.assertRaisesRegex(ParseError,"constant index"):
            parse_bytes(chunk(function(words=[0x19 << 25,0x12020000])))

    def test_closure_index_outside_array(self):
        with self.assertRaisesRegex(ParseError,"closure index"):
            parse_bytes(chunk(function(words=[0x3c << 25,0x12020000])))

    def test_branch_outside_function(self):
        with self.assertRaisesRegex(ParseError,"branch target"):
            parse_bytes(chunk(function(words=[(0x1c << 25) | (65533 << 8)])))

    def test_valid_branch_target(self):
        out=parse_bytes(chunk(function(words=[(0x1c << 25) | (65535 << 8),0x12020000])))
        self.assertEqual(out["chunk"]["root_function"]["instructions"][0]["branch_target_pc_provisional"],1)

    def test_inconsistent_parameter_count(self):
        with self.assertRaisesRegex(ParseError,"register or upvalue"):
            parse_bytes(chunk(function(params=2)))

    def test_file_budget(self):
        with self.assertRaisesRegex(ParseError,"file exceeds"):
            parse_bytes(chunk(),Limits(max_file_bytes=10))

    def test_string_budget(self):
        with self.assertRaisesRegex(ParseError,"length exceeds"):
            parse_bytes(chunk(),Limits(max_string_bytes=3))

    def test_instruction_budget(self):
        with self.assertRaisesRegex(ParseError,"instruction count"):
            parse_bytes(chunk(function(words=[0x12020000,0x12020000])),Limits(max_instructions=1))

    def test_constant_budget(self):
        with self.assertRaisesRegex(ParseError,"constant count"):
            parse_bytes(chunk(function(constants=[b"\0",b"\0"])),Limits(max_constants=1))

    def test_depth_budget(self):
        with self.assertRaisesRegex(ParseError,"nesting"):
            parse_bytes(chunk(function(children=[function()])),Limits(max_depth=0))

    def test_total_function_budget(self):
        with self.assertRaisesRegex(ParseError,"total function count"):
            parse_bytes(chunk(function(children=[function()])),Limits(max_functions=1))

    def test_nonempty_debug_arrays_explicitly_unsupported(self):
        with self.assertRaisesRegex(ParseError,"debug arrays"):
            parse_bytes(chunk(function(debug=(1,0,0))))

    def test_nonempty_structures_explicitly_unsupported(self):
        with self.assertRaisesRegex(ParseError,"structure declarations"):
            parse_bytes(chunk(trailer=be(1)+string("example")))

    def test_changed_trailer_rejected(self):
        with self.assertRaisesRegex(ParseError,"trailer marker"):
            parse_bytes(chunk(trailer=be(2)+string(None)))

    def test_actual_read_bounded_when_file_grows_after_stat(self):
        fake=MagicMock()
        fake.stat.return_value.st_size=1
        stream=MagicMock(wraps=io.BytesIO(b"x"*100))
        fake.open.return_value.__enter__.return_value=stream
        with self.assertRaisesRegex(ParseError,"file exceeds"):
            parse_file(fake,Limits(max_file_bytes=10))
        stream.read.assert_called_once_with(11)

    def test_cli_refuses_output_hardlinked_to_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/"input.bin"
            alias=Path(tmp)/"output.json"
            original=wrapper(chunk())
            source.write_bytes(original)
            os.link(source,alias)
            with patch.object(sys,"argv",["amalur_script",str(source),"--output",str(alias)]),patch("sys.stderr",new_callable=io.StringIO),self.assertRaises(SystemExit) as caught:
                main()
            self.assertEqual(caught.exception.code,2)
            self.assertEqual(source.read_bytes(),original)

    def test_cli_refuses_hardlinked_output_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/"input.bin"
            json_path=Path(tmp)/"output.json"
            listing_path=Path(tmp)/"output.txt"
            source.write_bytes(wrapper(chunk()))
            json_path.write_bytes(b"keep")
            os.link(json_path,listing_path)
            with patch.object(sys,"argv",["amalur_script",str(source),"--output",str(json_path),"--disassembly",str(listing_path)]),patch("sys.stderr",new_callable=io.StringIO),self.assertRaises(SystemExit) as caught:
                main()
            self.assertEqual(caught.exception.code,2)
            self.assertEqual(json_path.read_bytes(),b"keep")


class RealSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=Path(os.environ.get("AMALUR_SCRIPT_SAMPLES",Path.home()/"Documents"/"Opem Amalur"/"work"/"script-samples"))
        if not cls.directory.exists():
            raise unittest.SkipTest("Windows extracted samples are unavailable")

    def check_sample(self,name,sha,counts):
        path=self.directory/name
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(before,sha,"fixture changed; investigate before updating expectations")
        result=parse_file(path)
        self.assertEqual(result["chunk"]["summary"],counts)
        self.assertEqual(result["chunk"]["payload_bytes_consumed"],result["chunk"]["payload_bytes"])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)

    def test_small_real_sample(self):
        self.check_sample("1596600.lua_bxml","445a889b4130c87c63dc9f2d249dd66c2b76d75e4729574747a7131dd23f807a",{"functions":2,"instructions":27,"constants":20})

    def test_large_real_sample(self):
        self.check_sample("441939.lua_bxml","88e5baf1fb05dae012799fe3ec5afb9e831a9444d22d0092b3db9880dc84bf8c",{"functions":154,"instructions":2622,"constants":1538})


if __name__=="__main__":
    unittest.main(verbosity=2)
