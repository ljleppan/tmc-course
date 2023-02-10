def test_test_resources_available(test_resource_dir):
    assert (test_resource_dir / "test_test.txt").read_text().startswith("foo")
