import pytest

from discord_bot import format_discord_message
from utils import (
    extract_search_results_from_file_path,
    compare_search_results,
    extract_json_from_string,
)


@pytest.fixture
def added_list():
    added_list = [
        "res/search_inventory_availability_In Stock_usage_Used_20241008-180105.html",
        "res/search_inventory_availability_In Stock_usage_Used_20241008-180604.html",
    ]
    return added_list


@pytest.fixture
def removed_list():
    removed_list = [
        "res/search_inventory_availability_In Stock_usage_Used_20241003-220104.html",
        "res/search_inventory_availability_In Stock_usage_Used_20241003-200345.html",
    ]
    return removed_list


def test_bike_is_added(added_list):
    """
    :return:
    """
    file_old, file_new = added_list
    res_old = extract_search_results_from_file_path(file_old)
    res_new = extract_search_results_from_file_path(file_new)
    # assert res_old != res_new
    diff = compare_search_results(new_results=res_new, old_results=res_old)
    assert len(diff["added"]) == 1

    item = diff["added"][0]
    json_item = extract_json_from_string(item)
    print(json_item)

    formatted_message = format_discord_message(json_item)

    expected_message = """**2020 MT-10 - Yamaha**
Price: 8999.0
[Link](https://www.af1racingaustin.com/inventory/2020-yamaha-mt-10-austin-tx-78753-12716611i)"""

    assert formatted_message == expected_message


def test_bike_is_removed():
    """TODO"""
    pass


def test_bike_removed_and_added():
    """TODO"""
    pass
