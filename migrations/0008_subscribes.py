from yoyo import step

steps = [
    step(
        """
        CREATE TABLE subscribers (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        "DROP TABLE subscribers"
    )
]