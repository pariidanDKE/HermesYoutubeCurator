from hermes_youtube_curator.cli.guards import finalize_result


def test_finalize_result_success():
    result = finalize_result(
        {"run_status": "success", "foo": "bar"},
        required_keys={"run_status", "foo"},
    )
    assert result.exit_code == 0
    assert result.payload["run_status"] == "success"


def test_finalize_result_missing_key():
    result = finalize_result({"run_status": "success"}, required_keys={"run_status", "foo"})
    assert result.exit_code == 1
    assert result.payload["run_status"] == "failed"
