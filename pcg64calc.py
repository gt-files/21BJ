import random
from colorama import Fore, Style, init
import time
import numpy as np

# Initialize colorama
init()

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Card values for a single deck
NUM_DECKS = 1  # Number of decks in the shoe
SIMULATIONS = 10000  # Number of simulations for Monte Carlo
RTP = 0.995  # Return-to-Player factor (e.g., 99.5%)

# Mapping face cards and Ace to values
FACE_CARD_MAPPING = {
    'T': 10,  # Ten
    'J': 10,  # Jack
    'Q': 10,  # Queen
    'K': 10,  # King
    'A': 11   # Ace
}

# Set numpy to use PCG64 RNG
rng = np.random.default_rng(np.random.PCG64())

# Helper Functions
def hand_value(cards):
    """Calculate the total value of a hand, accounting for soft aces."""
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def simulate_dealer_hand_vectorized(dealer_card, shoe, num_simulations):
    """Vectorized simulation of dealer hands."""
    dealer_hands = np.full(num_simulations, dealer_card)
    dealer_totals = np.full(num_simulations, hand_value([dealer_card]))

    while True:
        hits = dealer_totals < DEALER_STAND
        if not np.any(hits):
            break

        new_cards = rng.choice(shoe, size=num_simulations)
        dealer_hands = np.where(hits, dealer_hands + new_cards, dealer_hands)
        dealer_totals = np.where(hits, dealer_totals + new_cards, dealer_totals)
        
        # Adjust for aces if total > 21
        aces_to_adjust = (dealer_totals > BLACKJACK) & (dealer_hands == 11)
        dealer_totals = np.where(aces_to_adjust, dealer_totals - 10, dealer_totals)

    return dealer_totals

def monte_carlo_ev(player_cards, dealer_card, shoe, action, simulations=SIMULATIONS):
    """
    Perform Monte Carlo simulations to estimate the EV for a given action.
    Returns the EV of the action, adjusted for RTP, along with benchmarking data.
    """
    player_total = hand_value(player_cards)
    ev = 0

    shoe_array = np.array(shoe)
    checkpoint_means = []

    print(f"\nAction: {action}, Player Total: {player_total}, Dealer Card: {dealer_card}")

    if action == "Stand":
        start_time = time.time()
        for checkpoint in range(10):
            sub_simulations = simulations // 10
            dealer_totals = simulate_dealer_hand_vectorized(dealer_card, shoe_array, sub_simulations)
            ev += np.sum((dealer_totals > BLACKJACK) | (player_total > dealer_totals))
            ev -= np.sum(player_total < dealer_totals)
            checkpoint_means.append(ev / ((checkpoint + 1) * sub_simulations))
            print(f"Checkpoint {checkpoint + 1}: Stand EV = {ev / ((checkpoint + 1) * sub_simulations):.5f}")
        elapsed_time = time.time() - start_time

    elif action == "Hit":
        start_time = time.time()
        for checkpoint in range(10):
            sub_simulations = simulations // 10
            new_cards = rng.choice(shoe_array, size=sub_simulations)
            new_totals = player_total + new_cards

            dealer_totals = simulate_dealer_hand_vectorized(dealer_card, shoe_array, sub_simulations)

            win_conditions = (new_totals <= BLACKJACK) & ((dealer_totals > BLACKJACK) | (new_totals > dealer_totals))
            lose_conditions = (new_totals <= BLACKJACK) & (new_totals < dealer_totals)
            bust_conditions = new_totals > BLACKJACK

            ev += np.sum(win_conditions)
            ev -= np.sum(lose_conditions)
            ev -= np.sum(bust_conditions)
            checkpoint_means.append(ev / ((checkpoint + 1) * sub_simulations))
            print(f"Checkpoint {checkpoint + 1}: Hit EV = {ev / ((checkpoint + 1) * sub_simulations):.5f}")
        elapsed_time = time.time() - start_time

    elif action == "Double Down":
        start_time = time.time()
        for checkpoint in range(10):
            sub_simulations = simulations // 10
            new_cards = rng.choice(shoe_array, size=sub_simulations)
            new_totals = player_total + new_cards

            dealer_totals = simulate_dealer_hand_vectorized(dealer_card, shoe_array, sub_simulations)

            win_conditions = (new_totals <= BLACKJACK) & ((dealer_totals > BLACKJACK) | (new_totals > dealer_totals))
            lose_conditions = (new_totals <= BLACKJACK) & (new_totals < dealer_totals)
            bust_conditions = new_totals > BLACKJACK

            ev += 2 * np.sum(win_conditions)
            ev -= 2 * np.sum(lose_conditions)
            ev -= 2 * np.sum(bust_conditions)
            checkpoint_means.append(ev / ((checkpoint + 1) * sub_simulations))
            print(f"Checkpoint {checkpoint + 1}: Double Down EV = {ev / ((checkpoint + 1) * sub_simulations):.5f}")
        elapsed_time = time.time() - start_time

    elif action == "Split":
        start_time = time.time()
        split_ev = 0
        for _ in range(2):  # Simulate two split hands
            for checkpoint in range(10):
                sub_simulations = simulations // 10
                split_card = player_cards[0]
                new_cards = rng.choice(shoe_array, size=sub_simulations)
                new_totals = split_card + new_cards

                dealer_totals = simulate_dealer_hand_vectorized(dealer_card, shoe_array, sub_simulations)

                win_conditions = (new_totals <= BLACKJACK) & ((dealer_totals > BLACKJACK) | (new_totals > dealer_totals))
                lose_conditions = (new_totals <= BLACKJACK) & (new_totals < dealer_totals)
                bust_conditions = new_totals > BLACKJACK

                split_ev += np.sum(win_conditions)
                split_ev -= np.sum(lose_conditions)
                split_ev -= np.sum(bust_conditions)
            checkpoint_means.append(split_ev / ((checkpoint + 1) * sub_simulations * 2))
            print(f"Checkpoint {checkpoint + 1}: Split EV = {split_ev / ((checkpoint + 1) * sub_simulations * 2):.5f}")
        ev += split_ev / 2
        elapsed_time = time.time() - start_time

    print(f"Final EV for {action}: {ev / simulations:.5f}, Time: {elapsed_time:.2f}s\n")

    return (ev / simulations) * RTP, elapsed_time, checkpoint_means

# Main Gameplay Logic
def get_player_action(player_cards, dealer_card, shoe, is_first_turn=True):
    """Determines the player's optimal action based on Monte Carlo EV."""
    actions = ["Stand", "Hit"]

    # Only offer "Double Down" on the first turn
    if is_first_turn:
        actions.append("Double Down")

    # Only offer "Split" if the player's hand is a pair
    if len(player_cards) == 2 and player_cards[0] == player_cards[1]:
        actions.append("Split")

    evs = {}
    times = {}
    checkpoints = {}
    for action in actions:
        ev, elapsed_time, checkpoint_means = monte_carlo_ev(player_cards, dealer_card, shoe, action)
        evs[action] = ev
        times[action] = elapsed_time
        checkpoints[action] = checkpoint_means

    sorted_actions = sorted(evs.items(), key=lambda item: item[1], reverse=True)
    best_action = sorted_actions[0][0]
    second_best_action = sorted_actions[1][0] if len(sorted_actions) > 1 else None

    # Calculate EVdiff
    ev_diff = sorted_actions[0][1] - sorted_actions[1][1] if len(sorted_actions) > 1 else 0

    print("\nPlayer Cards:", player_cards, "Total:", hand_value(player_cards))
    print("Dealer Card:", dealer_card)
    print("Expected Values (EVs):")
    for action, ev in evs.items():
        if action == best_action:
            print(f"  {Fore.GREEN}{action}: {ev:.5f} ({times[action]:.2f}s) {Style.RESET_ALL}")
        else:
            print(f"  {action}: {ev:.5f} ({times[action]:.2f}s)")
        print(f"    Checkpoint Means: {checkpoints[action]}")
    print(f"    EVdiff: {ev_diff:.5f} VS ({second_best_action})")
    print("")
    print(f"Optimal Action: {best_action} ({times[best_action]:.2f} seconds)")

    return best_action

def main():
    print("Blackjack Optimal Strategy Solver with Monte Carlo EV Calculation and RTP Adjustment\n")

    while True:
        # ----------------------------------------------------------
        # RE-INITIALIZE the shoe each round to avoid depletion errors
        # ----------------------------------------------------------
        shoe = DECK * NUM_DECKS
        backup_shoe = shoe[:]

        try:
            # 1) Dealer card: single character
            dealer_card_input = input(
                "Enter Dealer's visible card (2-9 or T/J/Q/K/A): "
            ).strip().upper()
            if len(dealer_card_input) != 1:
                raise ValueError("Dealer input must be exactly 1 character!")
            # Convert that single character
            if dealer_card_input in FACE_CARD_MAPPING:
                dealer_card = FACE_CARD_MAPPING[dealer_card_input]
            elif dealer_card_input.isdigit() and 2 <= int(dealer_card_input) <= 9:
                dealer_card = int(dealer_card_input)
            else:
                raise ValueError("Invalid dealer card input!")

            # 2) Player cards: interpret each character
            player_input = input(
                "Enter Player's cards as consecutive characters (e.g. 'T5', 'J9', '77'): "
            ).strip().upper()
            if len(player_input) == 0:
                raise ValueError("Player's hand cannot be empty!")

            player_cards = []
            for c in player_input:
                if c in FACE_CARD_MAPPING:
                    player_cards.append(FACE_CARD_MAPPING[c])
                elif c.isdigit() and 2 <= int(c) <= 9:
                    player_cards.append(int(c))
                else:
                    raise ValueError(f"Invalid player card input: '{c}'")

            # Remove the dealer card from the shoe, with debug prints
            print(f"\n[DEBUG] Shoe has {shoe.count(dealer_card)} of {dealer_card} before removing Dealer card.")
            if dealer_card in shoe:
                shoe.remove(dealer_card)
                print(f"[DEBUG] Removed Dealer card {dealer_card}. Now shoe has {shoe.count(dealer_card)} of {dealer_card} left.")
            else:
                raise ValueError(f"Dealer card {dealer_card} not found in the shoe!")

            # Remove the player cards from the shoe, with debug prints
            for card in player_cards:
                print(f"\n[DEBUG] Shoe has {shoe.count(card)} of {card} before removing Player card.")
                if card in shoe:
                    shoe.remove(card)
                    print(f"[DEBUG] Removed Player card {card}. Now shoe has {shoe.count(card)} of {card} left.")
                else:
                    raise ValueError(f"Player card {card} not found in the shoe!")

            # 3) Additional cards to remove: each character is one card
            remove_cards_input = input(
                "Enter cards to remove (e.g. 'T5') or 0 for none: "
            ).strip().upper()

            if remove_cards_input == "" or remove_cards_input == "0":
                adjusted_shoe = shoe[:]
            else:
                cards_to_remove = []
                for c in remove_cards_input:
                    if c in FACE_CARD_MAPPING:
                        cards_to_remove.append(FACE_CARD_MAPPING[c])
                    elif c.isdigit() and 2 <= int(c) <= 9:
                        cards_to_remove.append(int(c))
                    else:
                        raise ValueError(f"Invalid card to remove: '{c}'")

                adjusted_shoe = shoe[:]
                for c in cards_to_remove:
                    print(f"\n[DEBUG] Shoe has {adjusted_shoe.count(c)} of {c} before removing from shoe.")
                    if c in adjusted_shoe:
                        adjusted_shoe.remove(c)
                        print(f"[DEBUG] Removed {c}. Now shoe has {adjusted_shoe.count(c)} of {c} left.")
                    else:
                        raise ValueError(f"Card {c} not found in the shoe!")

            # 4) Determine optimal action
            while True:
                best_action = get_player_action(
                    player_cards,
                    dealer_card,
                    adjusted_shoe,
                    is_first_turn=(len(player_cards) == 2)
                )

                if best_action == "Stand":
                    print("\nYou chose to stand. Ending turn.")
                    break

                if best_action == "Hit":
                    new_card_input = input(
                        "\nEnter the next drawn card (2-9 or T/J/Q/K/A): "
                    ).strip().upper()
                    if len(new_card_input) != 1:
                        raise ValueError("Drawn card input must be 1 character!")

                    if new_card_input in FACE_CARD_MAPPING:
                        player_cards.append(FACE_CARD_MAPPING[new_card_input])
                    elif new_card_input.isdigit() and 2 <= int(new_card_input) <= 9:
                        player_cards.append(int(new_card_input))
                    else:
                        raise ValueError("Invalid drawn card input!")

                    # Check bust
                    if hand_value(player_cards) > BLACKJACK:
                        print(f"\nPlayer busted with a total of {hand_value(player_cards)}!")
                        break

                elif best_action == "Double Down":
                    random_card = random.choice(adjusted_shoe)
                    player_cards.append(random_card)
                    print(f"\nFinal hand after doubling down: {player_cards} (Total: {hand_value(player_cards)})")
                    break

                elif best_action == "Split":
                    print("\nYou chose to split!")
                    ev_split = monte_carlo_ev(player_cards, dealer_card, adjusted_shoe, "Split")
                    print(f"EV for split: {ev_split:.5f}")
                    break

            print("\nStarting next hand...\n")

        except ValueError as e:
            # If there's any error, restore the shoe backup
            shoe = backup_shoe
            print(f"Invalid input: {e}")
            print("Please try again.\n")
            continue

if __name__ == "__main__":
    main()