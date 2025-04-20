from . import db
from .models import Category

def init_default_categories():
    default_categories = [
        {"name": "Supermercado", "description": "Productos de supermercado"},
        {"name": "Salud y Belleza", "description": "Productos de salud y belleza"},
        {"name": "Hogar y Oficina", "description": "Productos para el hogar y oficina"},
        {"name": "Moda", "description": "Productos de moda y vestimenta"},
        {"name": "Electrónicos", "description": "Productos electrónicos"},
        {"name": "Videojuegos", "description": "Productos de gaming"},
        {"name": "Bebés", "description": "Productos para bebés"},
        {"name": "Deportes", "description": "Artículos deportivos"},
        {"name": "Jardín y Exterior", "description": "Productos para jardín y exterior"}
    ]

    for category_data in default_categories:
        existing = Category.query.filter_by(name=category_data["name"]).first()
        if not existing:
            category = Category(**category_data)
            db.session.add(category)
    
    try:
        db.session.commit()
        print("Categorías por defecto creadas exitosamente")
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear categorías: {e}")