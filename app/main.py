import re

from app.db import engine
from app.models import metadata, users, history, word_bank
from sqlalchemy import select, insert, update
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

# NOTE: table creation/versioning is handled by Alembic migrations
# (see alembic/versions/). We don't call metadata.create_all() here.



def insert_user(name, email, password):
    with engine.connect() as conn:
        try:
            hashed = generate_password_hash(password)
            stmt = insert(users).values(
                name=name,
                email=email,
                password=hashed,
            )
            result = conn.execute(stmt)
            conn.commit()
            return result.inserted_primary_key[0]
        except SQLAlchemyError:
            conn.rollback()
            raise


def check_if_exist(email, password):
    with engine.connect() as conn:
        try:
            stmt = select(users).where(users.c.email == email)
            row = conn.execute(stmt).first()
            if row is None:
                return False
            return check_password_hash(row.password, password)
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_user_id(email):
    with engine.connect() as conn:
        try:
            stmt = select(users.c.user_id).where(users.c.email == email)
            row = conn.execute(stmt).first()
            if row is None:
                return None
            return row.user_id
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_user_by_email(email):
    with engine.connect() as conn:
        try:
            stmt = select(users).where(users.c.email == email)
            row = conn.execute(stmt).first()
            if row is None:
                return None
            return dict(row._mapping)
        except SQLAlchemyError:
            conn.rollback()
            raise


def update_last_login(user_id):
    with engine.connect() as conn:
        try:
            stmt = (
                update(users)
                .where(users.c.user_id == user_id)
                .values(last_login=text_now())
            )
            conn.execute(stmt)
            conn.commit()
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_all_users():
    with engine.connect() as conn:
        try:
            stmt = select(users)
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]
        except SQLAlchemyError:
            conn.rollback()
            raise


def text_now():
    from sqlalchemy import text
    return text("CURRENT_TIMESTAMP")




def insert_history(user_id, input_text, sentiment_label, confidence_score):
    with engine.connect() as conn:
        try:
            stmt = insert(history).values(
                user_id=user_id,
                input_text=input_text,
                sentiment_label=sentiment_label,
                confidence_score=confidence_score,
            )
            result = conn.execute(stmt)
            conn.commit()
            return result.inserted_primary_key[0]
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_history_by_id(history_id):
    with engine.connect() as conn:
        try:
            stmt = select(history).where(history.c.id == history_id)
            row = conn.execute(stmt).first()
            if row is None:
                return None
            return dict(row._mapping)
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_history_by_user(user_id):
    with engine.connect() as conn:
        try:
            stmt = select(history).where(
                history.c.user_id == user_id,
                history.c.Deleted == False,
            ).order_by(history.c.created_at.desc())
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_history_by_email(email):
    with engine.connect() as conn:
        try:
            user_row = conn.execute(
                select(users.c.user_id).where(users.c.email == email)
            ).first()
            if user_row is None:
                return []

            stmt = select(history).where(
                history.c.user_id == user_row.user_id,
                history.c.Deleted == False,
            ).order_by(history.c.created_at.desc())
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]
        except SQLAlchemyError:
            conn.rollback()
            raise


def delete_history(history_id):
    with engine.connect() as conn:
        try:
            stmt = update(history).where(history.c.id == history_id).values(Deleted=True)
            conn.execute(stmt)
            conn.commit()
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_all_history():
    with engine.connect() as conn:
        try:
            stmt = select(history).where(history.c.Deleted == False)
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]
        except SQLAlchemyError:
            conn.rollback()
            raise




def insert_word(word, category, weight=1):
    if category not in ("happy", "sad"):
        raise ValueError("category must be 'happy' or 'sad'")
    with engine.connect() as conn:
        try:
            stmt = insert(word_bank).values(
                word=word.lower().strip(),
                category=category,
                weight=weight,
            )
            result = conn.execute(stmt)
            conn.commit()
            return result.inserted_primary_key[0]
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_all_words():
    with engine.connect() as conn:
        try:
            stmt = select(word_bank).where(word_bank.c.Deleted == False)
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]
        except SQLAlchemyError:
            conn.rollback()
            raise


def get_words_by_category(category):
    with engine.connect() as conn:
        try:
            stmt = select(word_bank).where(
                word_bank.c.category == category,
                word_bank.c.Deleted == False,
            )
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]
        except SQLAlchemyError:
            conn.rollback()
            raise


def update_word_weight(word_id, weight):
    with engine.connect() as conn:
        try:
            stmt = update(word_bank).where(word_bank.c.id == word_id).values(weight=weight)
            conn.execute(stmt)
            conn.commit()
        except SQLAlchemyError:
            conn.rollback()
            raise





# ---------------------------------------------------------------------------
# sentiment analysis  -  logic-based, no ML/AI involved
# ---------------------------------------------------------------------------

# words that flip the polarity of the word that follows them
NEGATION_WORDS = {"not", "no", "never", "isn't", "wasn't", "aren't", "didn't", "don't", "doesn't", "can't", "won't"}

# words that scale up the weight of the word that follows them
INTENSIFIER_WORDS = {"very": 2, "extremely": 3, "really": 1.5, "so": 1.5, "super": 2}


def _tokenize(text_input):
    """Lowercase and split into plain word tokens (punctuation stripped)."""
    return re.findall(r"[a-zA-Z']+", text_input.lower())


def _build_lexicon():
    """Load the word bank into a lookup dict: {word: (category, weight)}."""
    words = get_all_words()
    return {w["word"]: (w["category"], w["weight"]) for w in words}


def analyze_sentiment(text_input, lexicon=None):
    """
    Compare each token in text_input against the word bank.
    Handles simple negation ("not happy") and intensifiers ("very sad").

    Returns a dict: {sentiment_label, confidence_score, score, matched_words}
    """
    if lexicon is None:
        lexicon = _build_lexicon()

    tokens = _tokenize(text_input)

    score = 0
    matched_words = []
    negate_next = False
    multiplier = 1

    for token in tokens:
        if token in NEGATION_WORDS:
            negate_next = True
            continue
        if token in INTENSIFIER_WORDS:
            multiplier = INTENSIFIER_WORDS[token]
            continue

        if token in lexicon:
            category, weight = lexicon[token]
            polarity = 1 if category == "happy" else -1

            if negate_next:
                polarity *= -1

            contribution = polarity * weight * multiplier
            score += contribution
            matched_words.append({"word": token, "category": category, "contribution": contribution})

        # each token resets the modifiers that only apply to the next word
        negate_next = False
        multiplier = 1

    if score > 0:
        sentiment_label = "positive"
    elif score < 0:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"

    # normalize confidence to a 0-1 range based on how many matched words
    # contributed and how strongly, capped at 1.0
    max_possible = sum(abs(m["contribution"]) for m in matched_words) or 1
    confidence_score = round(min(abs(score) / max_possible, 1.0), 2) if matched_words else 0.0

    return {
        "sentiment_label": sentiment_label,
        "confidence_score": confidence_score,
        "score": score,
        "matched_words": matched_words,
    }


def analyze_and_save(user_id, text_input):
    """Run the analysis and store the result in the history table."""
    result = analyze_sentiment(text_input)
    history_id = insert_history(
        user_id=user_id,
        input_text=text_input,
        sentiment_label=result["sentiment_label"],
        confidence_score=result["confidence_score"],
    )
    result["history_id"] = history_id
    return result


"""
if __name__ == "__main__":
    # seed a small starter word bank
    insert_word("happy", "happy", weight=2)
    insert_word("good", "happy", weight=1)
    insert_word("great", "happy", weight=2)
    insert_word("sad", "sad", weight=2)
    insert_word("bad", "sad", weight=1)
    insert_word("terrible", "sad", weight=2)

    new_user_id = insert_user(name="Mohammad", email="n@example.com", password="mypassword")
    print("Inserted user:", new_user_id)

    print("Login OK:", check_if_exist("n@example.com", "mypassword"))

    result = analyze_and_save(new_user_id, "I am not very happy today, it was a bad day")
    print("Analysis result:", result)

    print("History:", get_history_by_user(new_user_id))
"""