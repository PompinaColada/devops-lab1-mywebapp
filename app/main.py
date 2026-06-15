import argparse
import os
import contextlib
import aiomysql
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

parser = argparse.ArgumentParser(description="mywebapp - Simple Inventory Web Service")
parser.add_argument('--port', type=int, default=5200, help="Port to listen on")
parser.add_argument('--db-host', default='127.0.0.1', help="Database host")
parser.add_argument('--db-user', default='app_user', help="Database user")
parser.add_argument('--db-password', default='', help="Database password")
parser.add_argument('--db-name', default='inventory_db', help="Database name")

args, unknown = parser.parse_known_args()

db_pool = None


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        db_pool = await aiomysql.create_pool(
            host=args.db_host,
            port=3306,
            user=args.db_user,
            password=args.db_password,
            db=args.db_name,
            autocommit=True
        )
    except Exception as e:
        print(f"Error creating connection pool: {e}")
    yield
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()


app = FastAPI(lifespan=lifespan)


class ItemCreate(BaseModel):
    name: str
    quantity: int


@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Simple Inventory API</title>
</head>
<body>
    <h1>Simple Inventory Business Logic Endpoints</h1>
    <ul>
        <li><a href="/items">GET /items</a> - Get list of inventory items</li>
        <li>POST /items - Create a new inventory item (accepts JSON:
            <code>{"name": "string", "quantity": int}</code>)</li>
        <li>GET /items/{id} - Get details for a specific item</li>
    </ul>
</body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/items")
async def get_items(request: Request):
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id, name FROM inventory")
                items = await cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Inventory Items</title>
</head>
<body>
    <h1>Inventory Items</h1>
    <table border="1">
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
            </tr>
        </thead>
        <tbody>
"""
        for item in items:
            html += f"            <tr><td>{item['id']}</td><td>{item['name']}</td></tr>\n"
        html += """        </tbody>
    </table>
</body>
</html>
"""
        return HTMLResponse(content=html, status_code=200)
    else:
        return items


@app.post("/items", status_code=201)
async def create_item(item: ItemCreate):
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO inventory (name, quantity) VALUES (%s, %s)",
                    (item.name, item.quantity)
                )
                insert_id = cur.lastrowid
        return {"id": insert_id, "name": item.name, "quantity": item.quantity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")


@app.get("/items/{id}")
async def get_item(id: int, request: Request):
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id, name, quantity, created_at FROM inventory WHERE id = %s", (id,))
                item = await cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Item Details</title>
</head>
<body>
    <h1>Item Details</h1>
    <table border="1">
        <tr>
            <th>ID</th>
            <td>{item['id']}</td>
        </tr>
        <tr>
            <th>Name</th>
            <td>{item['name']}</td>
        </tr>
        <tr>
            <th>Quantity</th>
            <td>{item['quantity']}</td>
        </tr>
        <tr>
            <th>Created At</th>
            <td>{item['created_at']}</td>
        </tr>
    </table>
</body>
</html>
"""
        return HTMLResponse(content=html, status_code=200)
    else:
        if item.get("created_at"):
            item["created_at"] = item["created_at"].isoformat()
        return item


@app.get("/health/alive")
async def health_alive():
    return PlainTextResponse("OK", status_code=200)


@app.get("/health/ready")
async def health_ready():
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database pool not initialized")
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        return PlainTextResponse("Ready", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    app_host = os.environ.get("APP_HOST", "127.0.0.1")

    if os.environ.get("LISTEN_FDS"):
        print("Starting uvicorn under systemd socket activation on FD 3...")
        uvicorn.run("app.main:app", fd=3, log_level="info")
    else:
        print(f"Starting uvicorn on {app_host}:{args.port}...")
        uvicorn.run("app.main:app", host=app_host, port=args.port, log_level="info")
