from yoyo import step
steps = [
    step("""
        CREATE TABLE categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE
        )
    """, "DROP TABLE categories")
]