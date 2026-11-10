#!/usr/bin/env python3
"""
Smart Script Generator - Creates context-aware scripts and HTML structures
for the Amazing Cool Finds website.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

class SmartScriptGenerator:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.products_file = data_dir / "products.json"

    def load_products(self) -> List[Dict[str, Any]]:
        if not self.products_file.exists():
            return []
        with open(self.products_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def clean_title(self, title: str, limit: int = 60) -> str:
        """Trunca títulos largos de Amazon para mantener la limpieza visual."""
        if len(title) > limit:
            return title[:limit].rsplit(' ', 1)[0] + "..."
        return title

    def generate_product_card(self, product: Dict[str, Any]) -> str:
        """Genera una ficha de producto optimizada y limpia."""
        title = self.clean_title(product.get("title", "Cool Find"))
        price = product.get("price", "N/A")
        rating = product.get("rating", "N/A")
        image = product.get("image", "")
        link = product.get("link", "#")
        video_link = product.get("video_link", "#")

        return f"""
        <div class="product-card">
            <div class="product-image">
                <img src="{image}" alt="{title}" loading="lazy">
            </div>
            <div class="product-info">
                <h3>{title}</h3>
                <div class="product-meta">
                    <span class="rating">★ {rating}</span>
                    <span class="price">{price}</span>
                </div>
                <div class="product-actions">
                    <a href="{link}" target="_blank" class="btn-shop">Ver Oferta en Amazon 🔥</a>
                    <a href="{video_link}" target="_blank" class="btn-video">Ver Video 📺</a>
                </div>
            </div>
        </div>
        """

    def generate_category_section(self, category_name: str, products: List[Dict[str, Any]]) -> str:
        """Crea una sección organizada por categoría en lugar de un grid mezclado."""
        if not products:
            return ""

        # Mostramos solo los 4 mejores productos por categoría en la Home
        top_products = products[:4]
        cards_html = "".join([self.generate_product_card(p) for p in top_products])
        
        # Link a la página completa de la categoría (ej: tech.html)
        category_page = f"{category_name.lower().replace(' & ', '').replace(' ', '_')}.html"

        return f"""
        <section class="category-section">
            <div class="section-header">
                <h2>{category_name}</h2>
                <a href="{category_page}" class="view-all">Ver todos los {category_name} →</a>
            </div>
            <div class="product-grid">
                {cards_html}
            </div>
        </section>
        """

    def generate_home_page(self) -> str:
        """Genera la estructura de la Home Page optimizada."""
        products = self.load_products()
        if not products:
            return "<h1>No products found.</h1>"

        # 1. Crear sección de Destacados (Productos con rating > 4.5)
        featured = [p for p in products if float(p.get("rating", 0)) >= 4.5][:3]
        featured_html = "".join([self.generate_product_card(p) for p in featured])

        # 2. Organizar el resto por categorías
        categories = {}
        for p in products:
            cat = p.get("category", "General")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(p)

        category_sections_html = ""
        for cat_name, cat_prods in categories.items():
            category_sections_html += self.generate_category_section(cat_name, cat_prods)

        return f"""
        <div class="home-container">
            <!-- Sección de Impacto / Destacados -->
            <section class="featured-section">
                <div class="section-header">
                    <h2>🌟 Los Imprescindibles de la Semana</h2>
                    <p>Seleccionados por calidad, viralidad y precio.</p>
                </div>
                <div class="featured-grid">
                    {featured_html}
                </div>
            </section>

            <!-- Secciones Organizadas por Nichos -->
            <div class="all-categories">
                {category_sections_html}
            </div>
        </div>
        """

    def run(self, output_path: Path):
        """Ejecuta la generación del contenido."""
        home_html = self.generate_home_page()
        
        # Escribimos el resultado en index.html (u home.html según la config)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(home_html)
