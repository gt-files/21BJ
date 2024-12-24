import random

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Card values for a single deck
NUM_DECKS = 8  # Number of decks in the shoe
SIMULATIONS = 10000  # Number of simulations for Monte Carlo

# Mapping face cards and Ace to values
FACE_CARD_MAPPING = {'T': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}  # Aces treated as 11

# Helper Functions
def hand_value(cards):
    """Calculate the total value of a hand, accounting for soft aces."""
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def simulate_dealer_hand(dealer_hand, shoe):
    """Simulates the dealer's hand and returns the final value."""
    while hand_value(dealer_hand) < DEALER_STAND:
        dealer_hand.append(random.choice(shoe))
    return dealer_hand

def monte_carlo_ev(player_cards, dealer_card, shoe, action, simulations=SIMULATIONS):
    """
    Perform Monte Carlo simulations to estimate the EV for a given action.
    Returns the EV of the action.
    """
    player_total = hand_value(player_cards)
    ev = 0

    for _ in range(simulations):
        shoe_copy = shoe[:]
        random.shuffle(shoe_copy)

        if action == "Stand":
            dealer_hand = [dealer_card]
            dealer_hand = simulate_dealer_hand(dealer_hand, shoe_copy)
            dealer_total = hand_value(dealer_hand)
            if dealer_total > BLACKJACK or player_total > dealer_total:
                ev += 1  # Win
            elif player_total < dealer_total:
                ev -= 1  # Lose

        elif action == "Hit":
            player_cards_hit = player_cards + [random.choice(shoe_copy)]
            new_total = hand_value(player_cards_hit)
            if new_total > BLACKJACK:
                ev -= 1  # Bust
            else:
                dealer_hand = [dealer_card]
                dealer_hand = simulate_dealer_hand(dealer_hand, shoe_copy)
                dealer_total = hand_value(dealer_hand)
                if dealer_total > BLACKJACK or new_total > dealer_total:
                    ev += 1  # Win
                elif new_total < dealer_total:
                    ev -= 1  # Lose

        elif action == "Double Down":
            player_cards_double = player_cards + [random.choice(shoe_copy)]
            new_total = hand_value(player_cards_double)
            bet = 2  # Doubling the bet
            if new_total > BLACKJACK:
                ev -= bet  # Bust
            else:
                dealer_hand = [dealer_card]
                dealer_hand = simulate_dealer_hand(dealer_hand, shoe_copy)
                dealer_total = hand_value(dealer_hand)
                if dealer_total > BLACKJACK or new_total > dealer_total:
                    ev += bet  # Win
                elif new_total < dealer_total:
                    ev -= bet  # Lose

        elif action == "Split":
            split_ev = 0
            # Simulate dealer hand once for consistency across split simulations
            dealer_hand = [dealer_card]
            dealer_hand = simulate_dealer_hand(dealer_hand, shoe_copy)
            dealer_total = hand_value(dealer_hand)

            for _ in range(2):  # Simulate two split hands
                hand = [player_cards[0], random.choice(shoe_copy)]
                hand_total = hand_value(hand)
                if hand_total > BLACKJACK:
                    split_ev -= 1  # Bust
                elif dealer_total > BLACKJACK or hand_total > dealer_total:
                    split_ev += 1  # Win
                elif hand_total < dealer_total:
                    split_ev -= 1  # Lose
            ev += split_ev / 2  # Average EV of both hands

    return ev / simulations

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

    evs = {action: monte_carlo_ev(player_cards, dealer_card, shoe, action) for action in actions}
    sorted_actions = sorted(evs.items(), key=lambda item: item[1], reverse=True)
    best_action = sorted_actions[0][0]
    second_best_action = sorted_actions[1][0] if len(sorted_actions) > 1 else None

    # Calculate EVdiff
    ev_diff = sorted_actions[0][1] - sorted_actions[1][1] if len(sorted_actions) > 1 else 0

    print("\nPlayer Cards:", player_cards, "Total:", hand_value(player_cards))
    print("Dealer Card:", dealer_card)
    print("Expected Values (EVs):")
    for action, ev in evs.items():
        print(f"  {action}: {ev:.5f}")
    print(f"    EVdiff: {ev_diff:.5f} VS ({second_best_action})")  # New line for EVdiff with the second most optimal action
    print(f"")
    print(f"Optimal Action: {best_action}")
   

    return best_action

def main():
    print("Blackjack Optimal Strategy Solver with Monte Carlo EV Calculation\n")
    shoe = DECK * NUM_DECKS  # Simulate an 8-deck shoe

    while True:
        try:
            # Input for Dealer's visible card
            dealer_card_input = input("Enter Dealer's visible card (2-11, where 11 is Ace, T/J/Q/K for face cards): ").strip().upper()
            if dealer_card_input in FACE_CARD_MAPPING:
                dealer_card = FACE_CARD_MAPPING[dealer_card_input]
            elif dealer_card_input.isdigit() and 2 <= int(dealer_card_input) <= 11:
                dealer_card = int(dealer_card_input)
            else:
                raise ValueError("Invalid dealer card input!")

            # Input for Player's cards
            player_input = input("Enter Player's cards (use 11 for Ace, T/J/Q/K for face cards): ").strip().upper()
            player_cards = []

            for card in player_input:
                if card in FACE_CARD_MAPPING:
                    player_cards.append(FACE_CARD_MAPPING[card])
                elif card.isdigit() and 2 <= int(card) <= 11:
                    player_cards.append(int(card))
                else:
                    raise ValueError("Invalid player card input!")

            if len(player_cards) == 0:
                raise ValueError("Player's hand cannot be empty!")

            # Input for cards to remove from the shoe
            remove_cards_input = input("Enter cards to remove from the shoe (leave blank or enter 0 for none): ").strip().upper()
            if remove_cards_input == "" or remove_cards_input == "0":
                adjusted_shoe = shoe[:]
            else:
                cards_to_remove = []
                for card in remove_cards_input:
                    if card in FACE_CARD_MAPPING:
                        cards_to_remove.append(FACE_CARD_MAPPING[card])
                    elif card.isdigit() and 2 <= int(card) <= 11:
                        cards_to_remove.append(int(card))
                    else:
                        raise ValueError("Invalid card value to remove!")

                # Adjust the shoe by removing the specified cards
                adjusted_shoe = shoe[:]
                for card in cards_to_remove:
                    if card in adjusted_shoe:
                        adjusted_shoe.remove(card)
                    else:
                        raise ValueError(f"Card {card} not found in the shoe!")

            # Determine the optimal action using the adjusted shoe
            while True:
                best_action = get_player_action(player_cards, dealer_card, adjusted_shoe, is_first_turn=len(player_cards) == 2)

                if best_action == "Stand":
                    print("\nYou chose to stand. Ending turn.")
                    break

                if best_action == "Hit":
                    new_card = input("\nEnter the value of the next card drawn (T/J/Q/K for face cards, 2-11 for others): ").strip().upper()
                    if new_card in FACE_CARD_MAPPING:
                        player_cards.append(FACE_CARD_MAPPING[new_card])
                    else:
                        player_cards.append(int(new_card))
                    if hand_value(player_cards) > BLACKJACK:
                        print(f"\nPlayer busted with a total of {hand_value(player_cards)}!")
                        break

                elif best_action == "Double Down":
                    player_cards.append(random.choice(adjusted_shoe))
                    print(f"\nFinal hand after doubling down: {player_cards} (Total: {hand_value(player_cards)})")
                    break

                elif best_action == "Split":
                    print("\nYou chose to split!")
                    ev_split = monte_carlo_ev(player_cards, dealer_card, adjusted_shoe, "Split")
                    print(f"EV for split: {ev_split:.5f}")
                    break

            print("\nStarting next hand...\n")

        except ValueError as e:
            print(f"Invalid input: {e}")
            print("Please try again.\n")
            continue

if __name__ == "__main__":
    main()
