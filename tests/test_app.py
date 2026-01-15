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
    process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port", PORT, "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(5)  # Give the app time to start
    yield
    process.kill()

def test_ai_deploys_and_attacks(streamlit_app, page: Page):
    """
    Tests that the AI can deploy a card and then attack with it on a subsequent turn,
    using the updated rendering logic for verification.
    """
    page.goto(BASE_URL)

    # More specific locators targeting the horizontal blocks containing the cards
    ai_board = page.locator('div[data-testid="stHorizontalBlock"]').nth(0)
    player_board = page.locator('div[data-testid="stHorizontalBlock"]').nth(1)

    # --- TURN 1: Player Deploys an Intern ---
    page.get_by_role("button", name="Select").nth(1).click() # Select Intern
    page.get_by_role("button", name="Deploy Here").first.click()
    expect(player_board.get_by_text("Unpaid Intern")).to_be_visible(timeout=10000)

    # --- End Turn 1 ---
    page.get_by_role("button", name="End Turn").click()

    # --- End Turn 2 (Player does nothing to ramp AI caffeine) ---
    page.get_by_role("button", name="End Turn").click()

    # --- TURN 3: Player's Turn Starts ---
    sidebar = page.locator('[data-testid="stSidebar"]')
    expect(sidebar.get_by_text("Turn: 3")).to_be_visible(timeout=10000)

    # Verify the AI deployed its card. Now we can distinguish.
    # The AI should have deployed a card on turn 2 and turn 3.
    expect(ai_board.get_by_text("Busy working...")).to_have_count(2, timeout=10000)
    expect(ai_board.get_by_text("Empty Cubicle")).to_have_count(3)

    # --- End Turn 3 (Player does nothing again) ---
    page.get_by_role("button", name="End Turn").click()

    # --- TURN 4: Player's Turn Starts ---
    # The AI's card will now attack.
    log_container = sidebar.locator('[data-testid="stVerticalBlock"]').filter(has=page.get_by_text("Game Log"))
    expect(log_container).to_contain_text("AI's Unpaid Intern is attacking your Unpaid Intern!", timeout=10000)
    expect(log_container).to_contain_text("Your Unpaid Intern has been defeated!")

    # Verify the player's intern is gone from the board.
    expect(player_board.get_by_text("Unpaid Intern")).to_have_count(0)
