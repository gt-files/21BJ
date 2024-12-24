import math

# Constants
NUMBER_OF_DECKS = 6  # Set the number of decks being used in the game
CARDS_PER_DECK = 52

# Card value mappings for simplicity
FACE_CARD_VALUES = {
    'A': [1, 11],  # Ace can be 1 or 11
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
    def __init__(self, decks=NUMBER_OF_DECKS):
        self.decks = decks
        self.total_cards = decks * CARDS_PER_DECK
        self.cards_dealt = 0
        self.running_count = 0

    def update_running_count(self, cards):
        """Update the running count based on the Hi-Lo card values."""
        cards = cards.upper()
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

# Main program
def main():
    print("Blackjack Card Counting Program")
    print("Enter cards dealt as a sequence (e.g., 'AK5T'). Type 'exit' to quit or 'reset' to reset all values.")

    counter = CardCounter()

    while True:
        user_input = input("Enter cards (or 'exit'/'reset'): ").strip()

        if user_input.lower() == 'exit':
            print("Exiting the program.")
            break
        elif user_input.lower() == 'reset':
            counter.reset()
        else:
            counter.update_running_count(user_input)

if __name__ == "__main__":
    main()
