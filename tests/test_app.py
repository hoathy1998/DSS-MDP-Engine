"""Drives the Streamlit demo headlessly through both pages."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


def start():
    app = AppTest.from_file(APP, default_timeout=60).run()
    assert not app.exception
    return app


def click(app, label):
    next(button for button in app.button if button.label == label).click()
    app.run()
    assert not app.exception
    return app


def table(app, column):
    return next(frame.value for frame in app.dataframe if column in frame.value.columns)


def test_case_runs_to_a_decision_following_the_recommendation():
    app = click(start(), "Tạo hồ sơ ngẫu nhiên")
    for _ in range(20):
        if not any(button.label == "Thực hiện" for button in app.button):
            break
        app = click(app, "Thực hiện")
    results = table(app, "Cách làm")
    assert list(results["Cách làm"]) == ["Lựa chọn của bạn", "Theo đúng MDP", "Cây quyết định (Fig. 8)"]
    # Following every recommendation is by definition the MDP run.
    assert results.iloc[0]["Lợi nhuận"] == results.iloc[1]["Lợi nhuận"]
    assert results.iloc[0]["Quyết định"] == results.iloc[1]["Quyết định"]


def test_recommendation_continues_after_deviating():
    app = click(start(), "Tạo hồ sơ ngẫu nhiên")
    assert app.main.radio[0].value == ("do", "beta")
    app.main.radio[0].set_value(("do", "alpha"))
    app.run()
    app = click(app, "Thực hiện")
    actions = table(app, "Khuyến nghị")
    assert (actions["Khuyến nghị"] == "★").sum() == 1
    assert app.metric[0].value == "20.0"


def test_a_required_task_blocks_deciding_at_the_start():
    app = click(start(), "Tạo hồ sơ ngẫu nhiên")
    assert not any("Quyết định" in action for action in table(app, "Khuyến nghị")["Hành động"])


def test_switching_y_variant_resets_the_case():
    app = click(start(), "Tạo hồ sơ ngẫu nhiên")
    app.sidebar.radio[1].set_value("margin_repair")
    app.run()
    assert not app.exception
    assert "case" not in app.session_state


def test_toy_page_shows_the_corrected_values():
    app = start()
    app.sidebar.radio[0].set_value("Ví dụ nhỏ của bài báo")
    app.run()
    assert not app.exception
    assert app.metric[0].value == "1.00"
    actions = table(app, "Khuyến nghị")
    recommended = actions[actions["Khuyến nghị"] == "★"].iloc[0]
    assert recommended["Hành động"] == "Quyết định: nhận (f = 1)"

    app.selectbox[1].set_value(4)
    app.run()
    assert app.metric[0].value == "2.50"
