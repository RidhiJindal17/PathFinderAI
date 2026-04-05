import srsly
try:
    from srsly.msgpack import _unpacker
    print("SUCCESS: srsly.msgpack._unpacker imported successfully")
except ImportError as e:
    print(f"FAILURE: {e}")
except Exception as e:
    print(f"ERROR: {e}")
