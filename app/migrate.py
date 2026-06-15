import asyncio
import argparse
import aiomysql


async def run_migration():
    parser = argparse.ArgumentParser(description="MariaDB Migration Script")
    parser.add_argument('--db-host', default='127.0.0.1', help="Database host")
    parser.add_argument('--db-user', default='app_user', help="Database user")
    parser.add_argument('--db-password', default='', help="Database password")
    parser.add_argument('--db-name', default='inventory_db', help="Database name")

    args = parser.parse_args()

    print(f"Connecting to MariaDB at host {args.db_host}...")

    try:
        conn = await aiomysql.connect(
            host=args.db_host,
            user=args.db_user,
            password=args.db_password,
            autocommit=True
        )
    except Exception as e:
        print(f"Failed to connect to MariaDB host to check database existence: {e}")
        return

    async with conn.cursor() as cur:
        print(f"Ensuring database '{args.db_name}' exists...")
        await cur.execute(f"CREATE DATABASE IF NOT EXISTS {args.db_name}")

    conn.close()
    await conn.ensure_closed()

    try:
        conn = await aiomysql.connect(
            host=args.db_host,
            user=args.db_user,
            password=args.db_password,
            db=args.db_name,
            autocommit=True
        )
    except Exception as e:
        print(f"Failed to connect to database '{args.db_name}': {e}")
        return

    async with conn.cursor() as cur:
        print("Ensuring table 'inventory' exists...")
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                quantity INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Database migrations applied successfully.")

    conn.close()
    await conn.ensure_closed()


if __name__ == "__main__":
    asyncio.run(run_migration())
