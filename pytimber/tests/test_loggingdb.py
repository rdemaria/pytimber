import pytimber


def test_loggingdb():

    ldb = pytimber.LoggingDB()

    result = ldb.search('HX:BETA%')
    expected = [
        'HX:BETASTAR_IP1', 'HX:BETASTAR_IP2', 'HX:BETASTAR_IP5',
        'HX:BETASTAR_IP8']
    assert result == expected
