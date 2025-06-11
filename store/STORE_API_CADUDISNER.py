# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING

MONGO_DETAILS = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.store
db_products = database.get_collection("products")

# app/models.py
from pydantic import BaseModel, Field
from typing import Optional

class ProductModel(BaseModel):
    name: str = Field(...)
    description: Optional[str] = Field(None)
    price: float = Field(..., gt=0)
    in_stock: bool = Field(default=True)

class ProductDB(ProductModel):
    id: str

    class Config:
        orm_mode = True

# app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class ProductSchema(BaseModel):
    name: str = Field(...)
    description: Optional[str] = Field(None)
    price: float = Field(..., gt=0)
    in_stock: bool = Field(default=True)

class ProductUpdateSchema(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]
    in_stock: Optional[bool]

class ProductOutSchema(ProductSchema):
    id: str

# app/crud.py
from bson import ObjectId
from app.database import db_products

def product_helper(product) -> dict:
    return {
        "id": str(product["_id"]),
        "name": product["name"],
        "description": product.get("description"),
        "price": product["price"],
        "in_stock": product["in_stock"]
    }

async def retrieve_products():
    products = []
    async for product in db_products.find().sort("name", 1):
        products.append(product_helper(product))
    return products

async def retrieve_product(id: str):
    product = await db_products.find_one({"_id": ObjectId(id)})
    if product:
        return product_helper(product)

async def add_product(product_data: dict):
    new_product = await db_products.insert_one(product_data)
    created = await db_products.find_one({"_id": new_product.inserted_id})
    return product_helper(created)

async def update_product(id: str, data: dict):
    if len(data) < 1:
        return False
    product = await db_products.find_one({"_id": ObjectId(id)})
    if product:
        updated = await db_products.update_one({"_id": ObjectId(id)}, {"$set": data})
        if updated:
            return True
    return False

async def delete_product(id: str):
    product = await db_products.find_one({"_id": ObjectId(id)})
    if product:
        await db_products.delete_one({"_id": ObjectId(id)})
        return True
    return False

# app/routers/products.py
from fastapi import APIRouter, HTTPException
from app.crud import *
from app.schemas import ProductSchema, ProductUpdateSchema, ProductOutSchema

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", response_model=list[ProductOutSchema])
async def get_products():
    return await retrieve_products()

@router.get("/{id}", response_model=ProductOutSchema)
async def get_product(id: str):
    product = await retrieve_product(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=ProductOutSchema, status_code=201)
async def create_product(product: ProductSchema):
    return await add_product(product.dict())

@router.put("/{id}", response_model=bool)
async def update_existing_product(id: str, product: ProductUpdateSchema):
    return await update_product(id, product.dict(exclude_unset=True))

@router.delete("/{id}", response_model=bool)
async def delete_existing_product(id: str):
    return await delete_product(id)

# app/main.py
from fastapi import FastAPI
from app.routers import products

app = FastAPI(title="Store API")
app.include_router(products.router)

# requirements.txt
fastapi
motor
pymongo
pydantic
uvicorn[standard]
pytest
httpx

# README.md
# Store API - FastAPI + MongoDB + TDD

## Executar localmente
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Testes
```bash
pytest
```

A API estará disponível em http://127.0.0.1:8000/docs
