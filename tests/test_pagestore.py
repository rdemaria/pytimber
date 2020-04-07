from pytimber.pagestore import PageStore


"""
def test_list():
    try:
        db = PageStore("test.db", "testdata")
        data = {"v1": ([1, 2, 3], [4, 5, 6]), "v2": ([1, 2, 3], [4, 5, 6])}

        db.store(data)
        data1 = db.get(["v1", "v2"])
        data2 = db.get("v%")
        assert len(data1) == 2
        assert len(data2) == 2

        assert set(data1.keys()) == set(data1.keys())
        assert data["v1"][0] == db.get("v1")["v1"]
    finally:
        db.delete()
"""
