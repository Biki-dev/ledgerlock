from services.kane_parser import parse_kane_output


def test_parse_successful_run():
    output = """{"type":"stream_start","surface":"run","v":1}
{"step":1,"status":"done","remark":"Login successful"}
{"step":2,"status":"done","remark":"Invoice opened"}
{"type":"run_end","status":"passed","summary":"Approval was blocked","reason":"Objective completed","duration":20.5,"credits_consumed":10}
"""

    result = parse_kane_output(output)

    assert result["run_end"]["status"] == "passed"
    assert len(result["steps"]) == 2
    assert result["steps"][0]["remark"] == "Login successful"


def test_parse_failed_run():
    output = """{"step":1,"status":"done","remark":"Login successful"}
{"step":2,"status":"failed","remark":"Invoice unexpectedly approved"}
{"type":"run_end","status":"failed","summary":"Approval bypass detected","reason":"Assertion failed","duration":30}
"""

    result = parse_kane_output(output)

    assert result["run_end"]["status"] == "failed"
    assert len(result["steps"]) == 2
    assert result["steps"][1]["remark"] == "Invoice unexpectedly approved"


def test_ignore_non_json_lines_and_keep_last_run_end():
    output = """Starting Kane
not json
{"type":"run_end","status":"failed"}
{"type":"run_end","status":"passed"}
"""

    result = parse_kane_output(output)

    assert len(result["events"]) == 2
    assert result["run_end"]["status"] == "passed"
