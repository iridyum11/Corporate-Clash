import re
from playwright.sync_api import Page, expect
import subprocess
import time
import pytest

PORT = "8501"
BASE_URL = f"http://localhost:{PORT}"

@pytest.fixture(scope="session")
def streamlit_app():
    """Fixture to start and stop the Streamlit app for the test session."""
    # Run Streamlit in headless mode for CI/CD environments
    process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port", PORT, "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(5)  # Give the app time to start
    yield
    process.kill()

def test_automated_game_loop_and_combat(streamlit_app, page: Page):
    """
    Tests a predictable game loop with corrected assertions based on game rules.
    """
    page.goto(BASE_URL)

    # --- TURN 1 ---
    # Player has 1 caffeine. Hand is [Micromanager, Intern]. Select the "Unpaid Intern".
    page.get_by_role("button", name="Select").nth(1).click()

    # Deploy to the first available slot.
    page.get_by_role("button", name="Deploy Here").first.click()

    # Verify intern is on the board.
    player_board = page.locator("section").filter(has=page.get_by_text("Your Department"))
    expect(player_board.get_by_text("Unpaid Intern")).to_be_visible(timeout=10000)

    # End Turn. The AI takes its turn but cannot play any cards (cost > 1 caffeine).
    page.get_by_role("button", name="End Turn").click()

    # --- TURN 2 ---
    # Verify we are in Turn 2.
    sidebar = page.locator('[data-testid="stSidebar"]')
    expect(sidebar.get_by_text("Turn: 2")).to_be_visible(timeout=10000)

    # The Intern can now attack. Find its "Select Attacker" button.
    player_board = page.locator("section").filter(has=page.get_by_text("Your Department"))
    intern_container = player_board.locator('[data-testid="stVerticalBlock"]').filter(has_text="Unpaid Intern")
    intern_container.get_by_role("button", name="Select Attacker").click()

    # Attack the first cubicle, which must be empty.
    ai_board = page.locator("section").filter(has=page.get_by_text("Opponent's Department"))
    ai_board.get_by_role("button", name="Target Cubicle 1").click()

    # Assert the log shows a direct hit to sanity, because the AI had no playable cards.
    log_container = sidebar.locator('[data-testid="stVerticalBlock"]').filter(has=page.get_by_text("Game Log"))
    expect(log_container).to_contain_text("The cubicle was empty!", timeout=10000)
    expect(log_container).to_contain_text("dealt 1 damage directly to the AI's Sanity")

    # Verify AI sanity is now 19.
    expect(sidebar.get_by_text("AI Sanity: 19/20")).to_be_visible()
