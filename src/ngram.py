"""
N-gram language model for Turkish text correction.
Provides context-aware probability scoring for word sequences.
"""
import pickle
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union


class NGramModel:
    """N-gram language model with backoff to lower-order models."""

    def __init__(self, max_order: int = 3):
        self.max_order = max_order
        # n-gram counts: {(w1, w2, ...,wn): count}
        self.ngram_counts: Dict[Tuple[str, ...], int] = defaultdict(int)
        # Context counts: {(w1, w2, ..., w{n-1}): count}
        self.context_counts: Dict[Tuple[str, ...], int] = defaultdict(int)
        # Vocabulary set
        self.vocab: set = set()
        # Backoff weights (for Kneser-Ney or similar smoothing)
        self.backoff_weight: Dict[Tuple[str, ...], float] = defaultdict(float)

    def load_from_text(self, text_lines: List[str], vocab_limit: int = 100000):
        """
        Load n-gram model from text lines.

        Args:
            text_lines: List of tokenized text lines
            vocab_limit: Maximum vocabulary size to keep
        """
        # Tokenize and build vocabulary
        all_tokens = []
        for line in text_lines:
            tokens = line.strip().split()
            if tokens:
                all_tokens.extend(tokens)
                self.vocab.update(tokens)

        # Limit vocabulary if needed
        if len(self.vocab) > vocab_limit:
            # Keep most frequent words
            word_freq = Counter(all_tokens)
            most_common = set(word for word, _ in word_freq.most_common(vocab_limit))
            self.vocab = most_common & self.vocab  # Intersection

        # Count n-grams
        for line in text_lines:
            tokens = line.strip().split()
            if not tokens:
                continue

            # Add sentence boundary tokens
            tokens = ['<s>'] + tokens + ['</s>']

            # Count n-grams for each order
            for order in range(1, self.max_order + 1):
                for i in range(len(tokens) - order + 1):
                    ngram = tuple(tokens[i:i + order])
                    self.ngram_counts[ngram] += 1

                    # Count context (all but last word)
                    if order > 1:
                        context = ngram[:-1]
                        self.context_counts[context] += 1

    def get_ngram_prob(self, ngram: Tuple[str, ...]) -> float:
        """
        Get probability of an n-gram with backoff.

        Args:
            ngram: Tuple of words

        Returns:
            Probability score
        """
        if len(ngram) > self.max_order:
            # Truncate to max order
            ngram = ngram[-self.max_order:]

        # Direct count if available
        count = self.ngram_counts.get(ngram, 0)
        if count > 0:
            if len(ngram) == 1:
                # Unigram probability
                total = sum(self.ngram_counts[w] for w in self.vocab if (w,) in self.ngram_counts)
                return count / max(total, 1)
            else:
                # N-gram probability: P(w_n | w_{n-1}...) = C(w_{n-1}w_n) / C(w_{n-1}...)
                context = ngram[:-1]
                context_count = self.context_counts.get(context, 0)
                if context_count > 0:
                    return count / context_count
                else:
                    # Backoff
                    return self._backoff_prob(ngram)
        else:
            # Zero count, use backoff
            return self._backoff_prob(ngram)

    def _backoff_prob(self, ngram: Tuple[str, ...]) -> float:
        """Calculate backoff probability."""
        if len(ngram) <= 1:
            # Uniform distribution over vocabulary for unigrams
            return 1.0 / max(len(self.vocab), 1)

        # Backoff to (n-1)-gram
        context = ngram[:-1]
        word = ngram[-1]

        # Get backoff weight for context
        bow = self.backoff_weight.get(context, 1.0)

        # Recursively get probability of (n-1)-gram
        if len(context) > 0:
            return bow * self.get_ngram_prob(context[1:] + (word,)) if len(context) > 1 else bow * self.get_ngram_prob((word,))
        else:
            return bow * self.get_ngram_prob((word,))

    def get_context_score(self, context: Tuple[str, ...], word: str) -> float:
        """
        Get score for a word given its context.

        Args:
            context: Tuple of preceding words
            word: Target word

        Returns:
            Score indicating how well word fits in context
        """
        if not context:
            # No context, return unigram probability
            return self.get_ngram_prob((word,))

        # Limit context to max_order-1
        if len(context) >= self.max_order:
            context = context[-(self.max_order - 1):]

        # Form n-gram
        ngram = context + (word,)
        return self.get_ngram_prob(ngram)

    def save(self, filepath: Union[str, Path]):
        """Save model to file."""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'max_order': self.max_order,
                'ngram_counts': dict(self.ngram_counts),
                'context_counts': dict(self.context_counts),
                'vocab': list(self.vocab),
                'backoff_weight': dict(self.backoff_weight)
            }, f)

    @classmethod
    def load(cls, filepath: Union[str, Path]):
        """Load model from file."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        model = cls(max_order=data['max_order'])
        model.ngram_counts = defaultdict(int, data['ngram_counts'])
        model.context_counts = defaultdict(int, data['context_counts'])
        model.vocab = set(data['vocab'])
        model.backoff_weight = defaultdict(float, data['backoff_weight'])
        return model


def create_basic_turkish_model() -> NGramModel:
    """
    Create a basic Turkish n-gram model from the existing word list.
    This is a simplified version - in practice, we'd want a proper corpus.
    """
    model = NGramModel(max_order=3)

    # Load from existing Turkish word list
    data_path = Path("src/data/turkish_words.txt.gz")
    if data_path.exists():
        import gzip
        try:
            with gzip.open(data_path, 'rt', encoding='utf-8') as f:
                lines = []
                for line in f:
                    line = line.strip()
                    # Filter out non-word lines (numbers, symbols, etc.)
                    if line and not line.replace('.', '').replace(',', '').isdigit():
                        # Keep only alphabetic characters and Turkish letters
                        if all(c.isalpha() or c in 'çğıöşüÇĞİÖŞÜ' for c in line):
                            lines.append(line)

                            # Limit to prevent excessive memory usage
                            if len(lines) >= 50000:
                                break

                if lines:
                    model.load_from_text(lines, vocab_limit=50000)
        except Exception as e:
            print(f"Warning: Could not load Turkish word data: {e}")
            # Fallback to minimal model
            model.vocab = {"bir", "iki", "üç", "ve", "veya", "ama", "fakat"}
            # Add some basic bigrams
            model.ngram_counts[("ve", "bir")] = 10
            model.ngram_counts[("bir", "iki")] = 8
            model.context_counts[("ve",)] = 10
            model.context_counts[("bir",)] = 8
    else:
        # Minimal fallback model
        model.vocab = {"merhaba", "dünya", "teşekkür", "ederim", "günaydın"}
        model.ngram_counts[("merhaba", "dünya")] = 5
        model.ngram_counts[("teşekkür", "ederim")] = 8
        model.context_counts[("merhaba",)] = 5
        model.context_counts[("teşekkür",)] = 8

    return model


# Global model instance
_ngram_model: Optional[NGramModel] = None


def get_ngram_model() -> NGramModel:
    """Get or create the global n-gram model."""
    global _ngram_model
    if _ngram_model is None:
        _ngram_model = create_basic_turkish_model()
    return _ngram_model


def get_word_probability(word: str, context: Tuple[str, ...] = ()) -> float:
    """
    Get probability of a word given context.

    Args:
        word: Target word
        context: Tuple of preceding words

    Returns:
        Probability score
    """
    model = get_ngram_model()
    return model.get_context_score(context, word)


def get_ngram_probability(ngram: Tuple[str, ...]) -> float:
    """
    Get probability of an n-gram.

    Args:
        ngram: Tuple of words

    Returns:
        Probability score
    """
    model = get_ngram_model()
    return model.get_ngram_prob(ngram)


if __name__ == "__main__":
    # Test the model
    model = get_ngram_model()
    print(f"Vocabulary size: {len(model.vocab)}")
    print(f"'merhaba' probability: {get_word_probability('merhaba'):.6f}")
    print(f"'dünya' probability: {get_word_probability('dünya'):.6f}")
    print(f"'merhaba dunia' probability: {get_ngram_probability(('merhaba', 'dünya')):.6f}")