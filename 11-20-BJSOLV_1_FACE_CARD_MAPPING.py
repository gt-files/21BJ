import random

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Card values for a single deck
NUM_DECKS = 8  # Updated number of decks
SIMULATIONS = 10000  # Number of simulations for Monte Carlo

# Mapping face cards and Ace to values
FACE_CARD_MAPPING = {'T': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}  # A is now treated as 11 (Ace)

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
    return hand_value(dealer_hand)

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

        # Simulate action
        if action == "Stand":
            dealer_hand = [dealer_card]
            dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
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
                dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
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
                dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
                if dealer_total > BLACKJACK or new_total > dealer_total:
                    ev += bet  # Win
                elif new_total < dealer_total:
                    ev -= bet  # Lose

        elif action == "Split":
            # Split only when the hand is a valid pair
            if len(player_cards) == 2 and player_cards[0] == player_cards[1]:
                split_ev = 0
                for _ in range(2):  # Simulate both split hands
                    hand_copy = [player_cards[0], random.choice(shoe_copy)]
                    split_ev += monte_carlo_ev(hand_copy, dealer_card, shoe_copy, "Stand", simulations // 2)
                ev += split_ev / 2  # Average EV of both split hands

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
    best_action = max(evs, key=evs.get)

    print("\nPlayer Cards:", player_cards, "Total:", hand_value(player_cards))
    print("Dealer Card:", dealer_card)
    print("Expected Values (EVs):")
    for action, ev in evs.items():
        print(f"  {action}: {ev:.5f}")  # Changed to display 4 decimals
    print(f"Optimal Action: {best_action}")

    return best_action

def main():
    print("Blackjack Optimal Strategy Solver with Monte Carlo EV Calculation\n")
    shoe = DECK * NUM_DECKS  # Simulate an 8-deck shoe

    while True:
        try:
            # Input for Dealer's visible card (with face card mapping)
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

            # Split input into individual characters
            for card in player_input:
                if card in FACE_CARD_MAPPING:
                    player_cards.append(FACE_CARD_MAPPING[card])  # Map face card to 10
                elif card.isdigit() and 2 <= int(card) <= 11:
                    player_cards.append(int(card))  # Convert numeric cards directly
                else:
                    raise ValueError("Invalid player card input!")

            if len(player_cards) == 0:
                raise ValueError("Player's hand cannot be empty!")

            if any(card < 1 or card > 11 for card in player_cards):
                raise ValueError("Invalid card value entered!")

            while True:
                best_action = get_player_action(player_cards, dealer_card, shoe, is_first_turn=len(player_cards) == 2)
                
                if best_action == "Stand":
                    print("\nYou chose to stand. Ending turn.")
                    break

                if best_action == "Hit":
                    new_card = input("\nEnter the value of the next card drawn (T/J/Q/K for face cards, 2-11 for others): ")
                    if new_card in FACE_CARD_MAPPING:
                        player_cards.append(FACE_CARD_MAPPING[new_card])
                    else:
                        player_cards.append(int(new_card))
                    if hand_value(player_cards) > BLACKJACK:
                        print(f"\nPlayer busted with a total of {hand_value(player_cards)}!")
                        break

                elif best_action == "Double Down":
                    player_cards.append(random.choice(shoe))
                    print(f"\nFinal hand after doubling down: {player_cards} (Total: {hand_value(player_cards)})")
                    break

                elif best_action == "Split":
                    print("\nYou chose to split!")
                    # Split the hand into two separate hands
                    player_card_1 = [player_cards[0], random.choice(shoe)]
                    player_card_2 = [player_cards[1], random.choice(shoe)]
                    print(f"Hand 1: {player_card_1} (Total: {hand_value(player_card_1)})")
                    print(f"Hand 2: {player_card_2} (Total: {hand_value(player_card_2)})")

                    # Now play both hands independently
                    while hand_value(player_card_1) <= BLACKJACK:
                        action_1 = get_player_action(player_card_1, dealer_card, shoe, is_first_turn=False)
                        if action_1 == "Stand":
                            break
                        elif action_1 == "Hit":
                            new_card = random.choice(shoe)
                            player_card_1.append(new_card)
                            print(f"Hand 1: {player_card_1} (Total: {hand_value(player_card_1)})")

                    while hand_value(player_card_2) <= BLACKJACK:
                        action_2 = get_player_action(player_card_2, dealer_card, shoe, is_first_turn=False)
                        if action_2 == "Stand":
                            break
                        elif action_2 == "Hit":
                            new_card = random.choice(shoe)
                            player_card_2.append(new_card)
                            print(f"Hand 2: {player_card_2} (Total: {hand_value(player_card_2)})")

                    break  # After split, the round ends

            print("\nStarting next hand...\n")

        except ValueError as e:
            print(f"Invalid input: {e}")
            print("Please try again.\n")
            continue  # Restart the loop if input is invalid

if __name__ == "__main__":
    main()
