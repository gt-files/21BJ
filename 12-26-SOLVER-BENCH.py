import random
from colorama import Fore, Style, init
import time
import numpy as np

# Initialize colorama
init()

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11])  # Card values for a single deck
NUM_DECKS = 8  # Number of decks in the shoe
SIMULATIONS = 10000  # Number of simulations for Monte Carlo
RTP = 0.995  # Return-to-Player factor (e.g., 99.5%)

# Mapping face cards and Ace to values
FACE_CARD_MAPPING = {'T': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}  # Aces treated as 11

# Helper Functions
def hand_value_vectorized(hands):
    """Calculate total hand values accounting for soft Aces in a vectorized manner."""
    totals = np.sum(hands, axis=1)
    aces = np.sum(hands == 11, axis=1)
    while np.any(totals > BLACKJACK) and np.any(aces > 0):
        adjust_mask = (totals > BLACKJACK) & (aces > 0)
        totals[adjust_mask] -= 10
        aces[adjust_mask] -= 1
    return totals

def simulate_dealer_hand_vectorized(dealer_card, shoe, num_simulations):
    """Simulate dealer hands for multiple games in parallel using NumPy."""
    dealer_hands = np.zeros((num_simulations, 10), dtype=int)
    dealer_hands[:, 0] = dealer_card
    totals = hand_value_vectorized(dealer_hands[:, :1])

    for i in range(1, 10):
        draw_mask = totals < DEALER_STAND
        if not np.any(draw_mask):
            break

        dealer_hands[draw_mask, i] = np.random.choice(shoe, size=np.sum(draw_mask))
        totals = hand_value_vectorized(dealer_hands[:, :i + 1])

    return hand_value_vectorized(dealer_hands)

def monte_carlo_ev(player_cards, dealer_card, shoe, action, simulations=SIMULATIONS):
    """Perform Monte Carlo simulations to estimate the EV for a given action."""
    player_total = hand_value_vectorized(np.array([player_cards]))[0]
    shoe = np.array(shoe)
    ev = 0

    if action == "Stand":
        dealer_totals = simulate_dealer_hand_vectorized(dealer_card, shoe, simulations)
        wins = (dealer_totals > BLACKJACK) | (player_total > dealer_totals)
        losses = (player_total < dealer_totals) & (dealer_totals <= BLACKJACK)
        ev = np.sum(wins) - np.sum(losses)

    elif action == "Hit":
        player_cards_hit = np.array(player_cards + [0])
        drawn_cards = np.random.choice(shoe, size=simulations)
        player_cards_hit[-1] = drawn_cards
        new_totals = hand_value_vectorized(player_cards_hit.reshape(simulations, -1))
        busts = new_totals > BLACKJACK

        dealer_totals = simulate_dealer_hand_vectorized(dealer_card, shoe, simulations)
        wins = ~busts & ((dealer_totals > BLACKJACK) | (new_totals > dealer_totals))
        losses = ~busts & (new_totals < dealer_totals) & (dealer_totals <= BLACKJACK)
        ev = np.sum(wins) - np.sum(losses)

    elif action == "Double Down":
        player_cards_double = np.array(player_cards + [0])
        drawn_cards = np.random.choice(shoe, size=simulations)
        player_cards_double[-1] = drawn_cards
        new_totals = hand_value_vectorized(player_cards_double.reshape(simulations, -1))
        busts = new_totals > BLACKJACK

        dealer_totals = simulate_dealer_hand_vectorized(dealer_card, shoe, simulations)
        wins = ~busts & ((dealer_totals > BLACKJACK) | (new_totals > dealer_totals))
        losses = ~busts & (new_totals < dealer_totals) & (dealer_totals <= BLACKJACK)
        ev = 2 * (np.sum(wins) - np.sum(losses))

    elif action == "Split":
        split_evs = []
        for _ in range(2):
            split_hand = np.array([player_cards[0], np.random.choice(shoe)])
            split_totals = hand_value_vectorized(np.array([split_hand]))
            dealer_totals = simulate_dealer_hand_vectorized(dealer_card, shoe, simulations)
            wins = (dealer_totals > BLACKJACK) | (split_totals > dealer_totals)
            losses = (split_totals < dealer_totals) & (dealer_totals <= BLACKJACK)
            split_evs.append(np.sum(wins) - np.sum(losses))
        ev = np.mean(split_evs)

    return (ev / simulations) * RTP

def get_player_action(player_cards, dealer_card, shoe, is_first_turn=True):
    """Determines the player's optimal action based on Monte Carlo EV."""
    actions = ["Stand", "Hit"]

    if is_first_turn:
        actions.append("Double Down")
    if len(player_cards) == 2 and player_cards[0] == player_cards[1]:
        actions.append("Split")

    start_time = time.time()
    evs = {action: monte_carlo_ev(player_cards, dealer_card, shoe, action) for action in actions}
    elapsed_time = time.time() - start_time

    sorted_actions = sorted(evs.items(), key=lambda item: item[1], reverse=True)
    best_action = sorted_actions[0][0]

    print("\nPlayer Cards:", player_cards, "Total:", hand_value_vectorized(np.array([player_cards]))[0])
    print("Dealer Card:", dealer_card)
    print("Expected Values (EVs):")
    for action, ev in evs.items():
        if action == best_action:
            print(f"  {Fore.GREEN}{action}: {ev:.5f}{Style.RESET_ALL}")
        else:
            print(f"  {action}: {ev:.5f}")
    print(f"Optimal Action: {best_action} ({elapsed_time:.2f} seconds)")

    return best_action

def main():
    print("Blackjack Optimal Strategy Solver with Monte Carlo EV Calculation and RTP Adjustment\n")
    shoe = DECK.tolist() * NUM_DECKS

    while True:
        try:
            dealer_card_input = input("Enter Dealer's visible card (2-11, where 11 is Ace, T/J/Q/K for face cards): ").strip().upper()
            dealer_card = FACE_CARD_MAPPING.get(dealer_card_input, int(dealer_card_input))

            player_input = input("Enter Player's cards (use 11 for Ace, T/J/Q/K for face cards): ").strip().upper()
            player_cards = [FACE_CARD_MAPPING.get(card, int(card)) for card in player_input]

            best_action = get_player_action(player_cards, dealer_card, shoe, is_first_turn=len(player_cards) == 2)
            if best_action == "Stand":
                print("\nYou chose to stand. Ending turn.")
                break

        except ValueError as e:
            print(f"Invalid input: {e}")
            continue

if __name__ == "__main__":
    main()
