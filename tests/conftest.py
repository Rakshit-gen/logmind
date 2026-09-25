import pytest

from logmind.spark_session import get_spark


@pytest.fixture(scope="session")
def spark():
    session = get_spark("logmind-tests")
    yield session
    session.stop()
