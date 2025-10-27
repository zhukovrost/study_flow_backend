"""
CRUD операции для категории
"""
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_category(db: Session, category_id: int) -> Optional[Category]:
    """Получить категорию по ID"""
    return db.query(Category).filter(Category.id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
    """Получить список категорий"""
    return db.query(Category).offset(skip).limit(limit).all()


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    """Получить категорию по имени"""
    return db.query(Category).filter(Category.name == name).first()


def create_category(db: Session, category: CategoryCreate) -> Category:
    """Создать новую категорию"""
    db_category = Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: CategoryUpdate) -> Optional[Category]:
    """Обновить категорию"""
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    
    update_data = category.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> bool:
    """Удалить категорию"""
    db_category = get_category(db, category_id)
    if not db_category:
        return False
    
    db.delete(db_category)
    db.commit()
    return True

