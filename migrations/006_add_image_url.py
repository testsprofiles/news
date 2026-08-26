from yoyo import step

steps = [
    step(
        "ALTER TABLE posts ADD COLUMN image_url TEXT;",
        "ALTER TABLE posts DROP COLUMN image_url;"
    )
]