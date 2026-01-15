import streamlit as st
import random
from database import card_database
from game_logic import resolve_combat

# --- GAME STATE INITIALIZATION ---
def initialize_game():
    """Sets up the initial game state in the session."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True

        # Core game stats
        st.session_state.player_sanity = 20
        st.session_state.ai_sanity = 20
        st.session_state.player_caffeine = 1
        st.session_state.ai_caffeine = 1
        st.session_state.turn = 1
        st.session_state.log = ["Welcome to Corporate Clash!"]

        # MVP: Hardcoded Decks
        # Create unique instances of cards for tracking
        deck = [dict(card, uid=f"{card['id']}_{i}") for i, card in enumerate(card_database * 4)]
        random.shuffle(deck)

        st.session_state.player_deck = deck[:10]
        st.session_state.ai_deck = deck[10:20]

        # Deterministic hands for predictable testing
        # Player gets a Micromanager (ID 1) and an Intern (ID 5)
        st.session_state.player_hand = [
            next(c for c in st.session_state.player_deck if c['id'] == 1),
            next(c for c in st.session_state.player_deck if c['id'] == 5)
        ]
        # Ensure the drawn cards are removed from the deck
        st.session_state.player_deck = [c for c in st.session_state.player_deck if c['uid'] not in [h['uid'] for h in st.session_state.player_hand]]

        # Sort AI deck for predictability and deal the 3 lowest ID cards
        st.session_state.ai_deck.sort(key=lambda x: x['id'])
        st.session_state.ai_hand = [st.session_state.ai_deck.pop(0) for _ in range(3)]

        # Boards (5 cubicles per side)
        st.session_state.player_board = [None] * 5
        st.session_state.ai_board = [{"card": None, "revealed": False} for _ in range(5)]

        # Add summoning sickness tracking
        for card in st.session_state.player_board:
            if card:
                card['can_attack'] = False

        # Player action tracking
        st.session_state.selected_card_hand_index = None
        st.session_state.selected_attacker_board_index = None
        st.session_state.error_message = None

# --- UI RENDERING ---

def render_card(card, index, is_player=True):
    """Renders a single card UI."""
    if card:
        st.markdown(f"**{card['name']}**")
        st.markdown(f"*{card['class']}*")
        st.markdown(f"**{card['attack']} / {card['defense']}**")
        st.markdown(f"Cost: {card['cost']}")
        if is_player:
            st.markdown(f"Can Attack: {'Yes' if card.get('can_attack', False) else 'No'}")
    else:
        st.markdown("Empty Cubicle")

# --- Main App ---
st.set_page_config(layout="wide")
st.title("Corporate Clash: The Battle for the Breakroom")

# Initialize the game if it hasn't been already
initialize_game()

# --- ACTION HANDLERS ---
def check_game_over():
    """Checks for win/loss conditions."""
    if st.session_state.player_sanity <= 0:
        st.session_state.game_over = True
        st.session_state.winner = "AI"
    elif st.session_state.ai_sanity <= 0:
        st.session_state.game_over = True
        st.session_state.winner = "Player"
    elif not st.session_state.player_deck and not st.session_state.player_hand and all(c is None for c in st.session_state.player_board):
        st.session_state.game_over = True
        st.session_state.winner = "AI" # Player has no more resources
    elif not st.session_state.ai_deck and not st.session_state.ai_hand and all(s['card'] is None for s in st.session_state.ai_board):
        st.session_state.game_over = True
        st.session_state.winner = "Player" # AI has no more resources

def ai_turn():
    """AI plays a card if possible."""
    # Find playable cards and empty slots
    playable_cards = [c for c in st.session_state.ai_hand if c['cost'] <= st.session_state.ai_caffeine]
    empty_slots = [i for i, slot in enumerate(st.session_state.ai_board) if slot['card'] is None]

    if playable_cards and empty_slots:
        card_to_play = random.choice(playable_cards)
        slot_to_fill = random.choice(empty_slots)

        st.session_state.ai_caffeine -= card_to_play['cost']
        st.session_state.ai_board[slot_to_fill]['card'] = card_to_play
        st.session_state.ai_hand.remove(card_to_play)
        st.session_state.log.insert(0, f"AI deployed a card to cubicle {slot_to_fill + 1}.")

def handle_end_turn():
    """Ends the player's turn, triggers the AI's turn, and starts the next player turn."""
    # AI Turn
    ai_turn()

    # Start Player's Next Turn
    st.session_state.turn += 1
    st.session_state.player_caffeine = st.session_state.turn # Simple caffeine ramp
    st.session_state.ai_caffeine = st.session_state.turn

    # Reset attack status for player cards
    for card in st.session_state.player_board:
        if card:
            card['can_attack'] = True

    # Player draws a card
    if st.session_state.player_deck:
        st.session_state.player_hand.append(st.session_state.player_deck.pop())
    else:
        st.session_state.log.insert(0, "Your deck is empty! You are in Burnout!")
        # Win/loss check will handle game over

    st.session_state.log.insert(0, f"--- Turn {st.session_state.turn} ---")
    st.session_state.selected_card_hand_index = None
    st.session_state.selected_attacker_board_index = None
    st.session_state.error_message = None
    check_game_over()

def handle_card_selection(index):
    card = st.session_state.player_hand[index]
    if st.session_state.player_caffeine >= card['cost']:
        st.session_state.selected_card_hand_index = index
        st.session_state.selected_attacker_board_index = None
        st.session_state.error_message = None
    else:
        st.session_state.error_message = "Not enough Caffeine to play this card!"
        st.session_state.selected_card_hand_index = None

def handle_deployment(board_index):
    hand_index = st.session_state.selected_card_hand_index
    if hand_index is not None:
        card_to_play = st.session_state.player_hand[hand_index]
        st.session_state.player_caffeine -= card_to_play['cost']
        card_to_play['can_attack'] = False
        st.session_state.player_board[board_index] = card_to_play
        st.session_state.player_hand.pop(hand_index)
        st.session_state.selected_card_hand_index = None
        st.session_state.log.insert(0, f"You deployed {card_to_play['name']}.")

def handle_attacker_selection(board_index):
    """Selects a player card on the board to be an attacker."""
    st.session_state.selected_attacker_board_index = board_index
    st.session_state.selected_card_hand_index = None
    st.session_state.error_message = None

def handle_attack(target_index):
    """Resolves an attack from a selected attacker to a target."""
    attacker_index = st.session_state.selected_attacker_board_index
    attacker_card = st.session_state.player_board[attacker_index]

    target_slot = st.session_state.ai_board[target_index]
    target_slot['revealed'] = True
    defender_card = target_slot['card']

    st.session_state.log.insert(0, f"{attacker_card['name']} is attacking slot {target_index + 1}.")

    if defender_card is None:
        # Direct attack on sanity if cubicle is empty
        damage_to_sanity = attacker_card['attack']
        st.session_state.ai_sanity -= damage_to_sanity
        st.session_state.log.insert(0, f"The cubicle was empty! {attacker_card['name']} dealt {damage_to_sanity} damage directly to the AI's Sanity.")
    else:
        # Regular combat with a defending card
        damage_to_defender, damage_to_attacker, log_message = resolve_combat(attacker_card, defender_card)
        st.session_state.log.insert(0, log_message)

        # Apply damage to the defender
        defender_card['defense'] -= damage_to_defender
        if defender_card['defense'] <= 0:
            overkill = abs(defender_card['defense'])
            st.session_state.log.insert(0, f"{defender_card['name']} has been fired (defeated)!")
            st.session_state.ai_board[target_index]['card'] = None
            if overkill > 0:
                st.session_state.ai_sanity -= overkill
                st.session_state.log.insert(0, f"Overkill damage! The AI's Sanity takes {overkill} damage.")

        # Apply recoil damage to the attacker
        if damage_to_attacker > 0:
            attacker_card['defense'] -= damage_to_attacker
            if attacker_card['defense'] <= 0:
                st.session_state.player_board[attacker_index] = None
                st.session_state.log.insert(0, f"{attacker_card['name']} was defeated by recoil damage!")

    # Mark attacker as having acted this turn
    if attacker_card: # It might have been destroyed by recoil
        attacker_card['can_attack'] = False
    st.session_state.selected_attacker_board_index = None
    check_game_over()

# --- GAME OVER UI ---
if st.session_state.get("game_over", False):
    winner = st.session_state.winner
    if winner == "Player":
        st.success("Congratulations! You have won the battle for the breakroom!")
    else:
        st.error("You have lost the battle. Your corporate sanity has been depleted.")

    if st.button("Play Again"):
        st.session_state.clear()
        initialize_game()
        st.rerun()
else:
    # --- AI Board ---
    st.subheader("Opponent's Department (AI)")
    ai_cols = st.columns(5)
    for i, slot in enumerate(st.session_state.ai_board):
        with ai_cols[i]:
            # If an attacker is chosen, show target buttons
            if st.session_state.selected_attacker_board_index is not None:
                if st.button(f"Target Cubicle {i+1}", key=f"target_{i}"):
                    handle_attack(i)
                    st.rerun()
            # Otherwise, show the normal card/hidden state
            elif not slot["revealed"]:
                st.markdown("*"*20)
                st.markdown("Busy working...")
                st.markdown("*"*20)
            else:
                render_card(slot["card"], i, is_player=False)

    # --- Player Board ---
    st.subheader("Your Department")
    player_cols = st.columns(5)
    for i, card in enumerate(st.session_state.player_board):
        with player_cols[i]:
            if card is None:
                if st.session_state.selected_card_hand_index is not None:
                    if st.button("Deploy Here", key=f"deploy_{i}"):
                        handle_deployment(i)
                        st.rerun()
                else:
                    render_card(None, i)
            else:
                render_card(card, i, is_player=True)
                if card.get('can_attack', False):
                    if st.button("Select Attacker", key=f"attack_{i}"):
                        handle_attacker_selection(i)
                        st.rerun()

    # --- Player's Hand ---
    st.subheader("Your Hand")
    if not st.session_state.player_hand:
        st.write("Your hand is empty.")
    else:
        hand_cols = st.columns(len(st.session_state.player_hand))
        for i, card in enumerate(st.session_state.player_hand):
            with hand_cols[i]:
                st.markdown(f"**{card['name']}** ({card['cost']} C)")
                st.markdown(f"{card['attack']} / {card['defense']}")
                if st.button(f"Select", key=f"hand_{i}"):
                    handle_card_selection(i)
                    st.rerun()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Game Info")
        if st.button("End Turn"):
            handle_end_turn()
            st.rerun()
        st.markdown(f"**Turn:** {st.session_state.turn}")
        st.progress(st.session_state.player_sanity / 20.0, text=f"Your Sanity: {st.session_state.player_sanity}/20")
        st.progress(st.session_state.ai_sanity / 20.0, text=f"AI Sanity: {st.session_state.ai_sanity}/20")
        st.markdown(f"**Your Caffeine:** {st.session_state.player_caffeine}")
        if st.session_state.error_message:
            st.error(st.session_state.error_message)
        st.header("Game Log")
        log_area = st.container(height=300)
        for message in reversed(st.session_state.log):
            log_area.write(message)
