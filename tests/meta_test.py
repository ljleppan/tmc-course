def test_test_resources_available(test_resource_path):
    assert (test_resource_path / "test_test.txt").read_text().startswith("foo")
