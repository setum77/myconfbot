# tests/conftest.py

import logging
import pytest

# @pytest.fixture(autouse=True)
# def disable_logging():
#     """Отключает логирование в тестах, чтобы не засорять вывод."""
#     logging.disable(logging.CRITICAL)
#     yield
#     logging.disable(logging.NOTSET)  # Восстанавливаем

@pytest.fixture(autouse=True)
def set_test_logging():
    logging.getLogger().setLevel(logging.WARNING)