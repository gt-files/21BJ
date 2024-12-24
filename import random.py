import random
from collections import Counter
import numpy as np

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Card values for a single deck
NUM_DECKS = 8  # Number of decks in the shoe
SIMULATIONS = 5000  # Number of simulations for Monte Carlo
RTP = 0.995  # Return to Player for strategy optimization

# Mapping face cards and Ace to values
FACE_CARD_MAPPING = {'T': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}  # Aces treated as 11

# Cache for EV calculations
ev_cache = {}

# Helper Functions
def hand_value(cards):
    """Calculate the total value of a hand, accounting for soft aces."""
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def validate_input_cards(input_cards, num_expected, card_type):
    """Validate card inputs to match expected length and valid card values."""
    if len(input_cards) != num_expected:
        print(f"Error: Please enter exactly {num_expected} card(s) for {card_type}.")
        return False
    for card in input_cards:
        if card not in FACE_CARD_MAPPING and not card.isdigit():
            print(f"Error: Invalid card '{card}' in {card_type}. Use T/J/Q/K/A or 2-9.")
            return False
    return True

def convert_cards_to_values(cards):
    """Convert card strings (e.g., T/J/Q/K/A) to their numeric values."""
    return [FACE_CARD_MAPPING[card] if card in FACE_CARD_MAPPING else int(card) for card in cards]

def simulate_dealer_hand(dealer_hand, shoe_array):
    """Simulates the dealer's hand and returns the final value."""
    while hand_value(dealer_hand) < DEALER_STAND:
        if len(shoe_array) == 0:
            raise ValueError("Shoe ran out of cards during dealer simulation.")
        dealer_hand.append(shoe_array[0])
        shoe_array = shoe_array[1:]
    return dealer_hand

def calculate_payout(player_total, dealer_total, blackjack_payout=1.5):
    """Calculate the payout based on player and dealer totals."""
    if player_total > BLACKJACK:
        return -1  # Player busts
    elif dealer_total > BLACKJACK or player_total > dealer_total:
        return blackjack_payout if player_total == BLACKJACK else 1
    elif player_total < dealer_total:
        return -1  # Player loses
    else:
        return 0  # Push

def monte_carlo_ev(player_cards, dealer_card, shoe, action, blackjack_payout=1.5, simulations=SIMULATIONS):
    """Perform Monte Carlo simulations using NumPy."""
    shoe_array = np.array(list(shoe.elements()))
    results = []

    for _ in range(simulations):
        np.random.shuffle(shoe_array)
        shoe_array_copy = shoe_array.copy()
        player_total = hand_value(player_cards)

        if action == "Stand":
            dealer_hand = [dealer_card]
            dealer_hand = simulate_dealer_hand(dealer_hand, shoe_array_copy)
            dealer_total = hand_value(dealer_hand)
            payout = calculate_payout(player_total, dealer_total, blackjack_payout)
            results.append(payout)

        elif action == "Hit":
            if len(shoe_array_copy) == 0:
                raise ValueError("Shoe ran out of cards during player simulation.")
            player_total = hand_value(player_cards + [shoe_array_copy[0]])
            if player_total > BLACKJACK:
                results.append(-1)
            else:
                shoe_array_copy = shoe_array_copy[1:]
                dealer_hand = [dealer_card]
                dealer_hand = simulate_dealer_hand(dealer_hand, shoe_array_copy)
                dealer_total = hand_value(dealer_hand)
                payout = calculate_payout(player_total, dealer_total, blackjack_payout)
                results.append(payout)

        elif action == "Double Down":
            bet = 2
            if len(shoe_array_copy) == 0:
                raise ValueError("Shoe ran out of cards during double down simulation.")
            player_total = hand_value(player_cards + [shoe_array_copy[0]])
            if player_total > BLACKJACK:
                results.append(-bet)
            else:
                shoe_array_copy = shoe_array_copy[1:]
                dealer_hand = [dealer_card]
                dealer_hand = simulate_dealer_hand(dealer_hand, shoe_array_copy)
                dealer_total = hand_value(dealer_hand)
                payout = calculate_payout(player_total, dealer_total, blackjack_payout)
                results.append(bet * payout)

        elif action == "Split":
            if len(shoe_array_copy) < 2:
                raise ValueError("Not enough cards to simulate a split hand.")
            split_ev = 0
            for _ in range(2):  # Simulate two split hands
                hand = [player_cards[0], shoe_array_copy[0]]
                shoe_array_copy = shoe_array_copy[1:]
                hand_total = hand_value(hand)
                if hand_total > BLACKJACK:
                    split_ev -= 1
                else:
                    dealer_hand = [dealer_card]
                    dealer_hand = simulate_dealer_hand(dealer_hand, shoe_array_copy)
                    dealer_total = hand_value(dealer_hand)
                    split_ev += 1 if dealer_total > BLACKJACK or hand_total > dealer_total else -1 if hand_total < dealer_total else 0
            results.append(split_ev / 2)

    return np.mean(results)

def main():
    print("Blackjack Optimal Strategy Solver with Monte Carlo EV Calculation\n")
    shoe = Counter(DECK * NUM_DECKS)
    removed_cards = []

    while True:
        try:
            # Input player's cards
            while True:
                player_input = input("\nEnter Player's cards (T/J/Q/K/A or 2-9, exactly 2 cards): ").strip().upper()
                player_cards = list(player_input)
                if validate_input_cards(player_cards, 2, "player cards"):
                    player_cards = convert_cards_to_values(player_cards)
                    break

            # Input dealer's card
            while True:
                dealer_input = input("Enter Dealer's visible card (T/J/Q/K/A or 2-9, exactly 1 card): ").strip().upper()
                dealer_card = list(dealer_input)
                if validate_input_cards(dealer_card, 1, "dealer card"):
                    dealer_card = convert_cards_to_values(dealer_card)[0]
                    break

            # Input cards to remove
            remove_input = input("Enter cards to remove for the next hand (T/J/Q/K/A or 2-9, press Enter to skip): ").strip().upper()
            if remove_input:
                removed_cards = list(remove_input)
                if not validate_input_cards(removed_cards, len(removed_cards), "removed cards"):
                    continue
                removed_cards = convert_cards_to_values(removed_cards)

            adjusted_shoe = Counter(DECK * NUM_DECKS)
            for card in removed_cards:
                adjusted_shoe[card] -= 1

            # Determine optimal action
            actions = ["Stand", "Hit", "Double Down"]
            if player_cards[0] == player_cards[1]:
                actions.append("Split")

            evs = {action: monte_carlo_ev(player_cards, dealer_card, adjusted_shoe, action, blackjack_payout=RTP * 1.5) for action in actions}
            sorted_evs = sorted(evs.items(), key=lambda x: x[1], reverse=True)

            best_action, second_best = sorted_evs[0], sorted_evs[1]

            print("\nExpected Values (EVs):")
            for action, ev in evs.items():
                print(f"  {action}: {ev:.5f}")
            print(f"Optimal Action: {best_action[0]}")
            print(f"EVdiff: {best_action[1] - second_best[1]:.5f} ({second_best[0]})")

        except Exception as e:
            print(f"Error: {e}. Restarting input sequence...\n")
            continue

if __name__ == "__main__":
    main()
