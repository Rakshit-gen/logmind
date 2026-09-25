from logmind.log_analysis import find_anomalies


def test_find_anomalies_ranks_by_error_count(spark):
    rows = [
        {"service": "checkout-api", "level": "ERROR", "message": "boom"},
        {"service": "checkout-api", "level": "ERROR", "message": "boom"},
        {"service": "checkout-api", "level": "ERROR", "message": "boom"},
        {"service": "auth-svc", "level": "ERROR", "message": "denied"},
        {"service": "checkout-api", "level": "INFO", "message": "fine"},
    ]
    df = spark.createDataFrame(rows)

    result = find_anomalies(df, top_n=5)

    assert result[0]["service"] == "checkout-api"
    assert result[0]["error_count"] == 3
    assert result[1]["service"] == "auth-svc"
    assert result[1]["error_count"] == 1


def test_find_anomalies_ignores_info_lines(spark):
    rows = [{"service": "auth-svc", "level": "INFO", "message": "fine"}]
    df = spark.createDataFrame(rows)

    result = find_anomalies(df, top_n=5)

    assert result == []
