from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="CBS PM Buddy API",
    description="A project management buddy built with FastAPI",
    version="0.1.0",
)


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float


# In-memory storage for demo purposes
_items: dict[int, ItemCreate] = {}
_next_id: int = 1


@app.get("/")
async def root():
    return {"message": "Welcome to CBS PM Buddy API", "docs": "/docs"}


@app.get("/items", response_model=list[ItemResponse])
async def list_items():
    return [
        ItemResponse(id=item_id, **item.model_dump())
        for item_id, item in _items.items()
    ]


@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate):
    global _next_id
    item_id = _next_id
    _next_id += 1
    _items[item_id] = item
    return ItemResponse(id=item_id, **item.model_dump())


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item not found")
    item = _items[item_id]
    return ItemResponse(id=item_id, **item.model_dump())


@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item not found")
    del _items[item_id]
