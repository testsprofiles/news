from yoyo import step

steps = [
    step(
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS image_url TEXT;",
        "ALTER TABLE posts DROP COLUMN IF EXISTS image_url;"
    )
]