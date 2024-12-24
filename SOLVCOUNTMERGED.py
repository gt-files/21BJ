import random
import math

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Card values for a single deck
NUM_DECKS = 6  # Number of decks in the shoe
SIMULATIONS = 10000  # Number of simulations for Monte Carlo
CARDS_PER_DECK = 52

# Card value mappings for simplicity
FACE_CARD_VALUES = {
    'A': 11,  # Ace treated as 11 in default mapping
    'K': 10,
    'Q': 10,
    'J': 10,
    'T': 10  # Ten represented as 'T'
}

# Hi-Lo card counting values
HI_LO_VALUES = {
    '2': 1, '3': 1, '4': 1, '5': 1, '6': 1,
    '7': 0, '8': 0, '9': 0,
    'T': -1, 'J': -1, 'Q': -1, 'K': -1, 'A': -1
}

class CardCounter:
    def __init__(self, decks=NUM_DECKS):
        self.decks = decks
        self.total_cards = decks * CARDS_PER_DECK
        self.cards_dealt = 0
        self.running_count = 0

    def update_running_count(self, cards):
        """Update the running count based on the Hi-Lo card values."""
        for card in cards:
            if card in HI_LO_VALUES:
                self.running_count += HI_LO_VALUES[card]
                self.cards_dealt += 1
            else:
                print(f"Invalid card input: {card}")
        self.display_stats()

    def reset(self):
        """Reset all values to initial state."""
        self.cards_dealt = 0
        self.running_count = 0
        print("\nAll values have been reset.")
        self.display_stats()

    def calculate_true_count(self):
        """Calculate the true count based on the remaining decks."""
        remaining_decks = max((self.total_cards - self.cards_dealt) / CARDS_PER_DECK, 1)
        return self.running_count / remaining_decks

    def display_stats(self):
        """Display the current card counting statistics."""
        remaining_decks = max((self.total_cards - self.cards_dealt) / CARDS_PER_DECK, 1)
        true_count = self.calculate_true_count()
        remaining_cards = self.total_cards - self.cards_dealt
        dealt_percentage = (self.cards_dealt / self.total_cards) * 100
        print("\nCurrent Statistics:")
        print(f"Running Count: {self.running_count}")
        print(f"True Count: {true_count:.2f}")
        print(f"Divisor (Remaining Decks): {remaining_decks:.2f}")
        print(f"Number of Cards Dealt: {self.cards_dealt} ({dealt_percentage:.2f}% of the shoe)")
        print(f"Number of Remaining Cards: {remaining_cards}")

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
            dealer_hand = [dealer_card]
            dealer_hand = simulate_dealer_hand(dealer_hand, shoe_copy)
            dealer_total = hand_value(dealer_hand)

            for _ in range(2):
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

    print("\nPlayer Cards:", player_cards, "Total:", hand_value(player_cards))
    print("Dealer Card:", dealer_card)
    print("Expected Values (EVs):")
    for action, ev in evs.items():
        print(f"  {action}: {ev:.5f}")
    print(f"\nOptimal Action: {best_action}")

    return best_action

# Main Program

def main():
    print("Merged Blackjack Program with Card Counting")
    print("Enter cards dealt as a sequence (e.g., 'AK5T'). Type 'exit' to quit or 'reset' to reset values.")

    counter = CardCounter()
    shoe = DECK * NUM_DECKS

    while True:
        user_input = input("Enter cards (or 'exit'/'reset'): ").strip().upper()

        if user_input.lower() == 'exit':
            print("Exiting the program.")
            break

        elif user_input.lower() == 'reset':
            counter.reset()
            shoe = DECK * NUM_DECKS  # Reset shoe as well

        else:
            try:
                # Update card counter
                counter.update_running_count(user_input)

                # Adjust shoe for removed cards
                adjusted_shoe = shoe[:]
                for card in user_input:
                    value = FACE_CARD_VALUES.get(card, int(card)) if card in FACE_CARD_VALUES else int(card)
                    if value in adjusted_shoe:
                        adjusted_shoe.remove(value)

                # Input dealer and player hands for Blackjack
                dealer_card_input = input("Enter Dealer's visible card: ").strip().upper()

                if dealer_card_input == "":
                    print("Using previous dealer card.")
                else:
                    dealer_card = FACE_CARD_VALUES.get(dealer_card_input, int(dealer_card_input))

                player_input = input("Enter Player's cards: ").strip().upper()
                player_cards = [FACE_CARD_VALUES.get(c, int(c)) for c in player_input]

                print("Calculating optimal action...")
                get_player_action(player_cards, dealer_card, adjusted_shoe, is_first_turn=len(player_cards) == 2)

            except ValueError as e:
                print(f"Invalid input: {e}")
                continue

if __name__ == "__main__":
    main()
