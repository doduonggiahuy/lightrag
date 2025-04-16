import os
from dotenv import load_dotenv
load_dotenv()  # Load biến môi trường từ file .env (bao gồm OPENAI_API_KEY và OPENAI_API_BASE)

import asyncio
import nest_asyncio
nest_asyncio.apply()

import logging
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

# Import các module cần thiết từ thư viện lightrag
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status

# Cấu hình thư mục lưu trữ dữ liệu của LightRAG
WORKING_DIR = "./lightRAG_data"
if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

# Cấu hình kết nối Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "12345678"

from neo4j import GraphDatabase

def fetch_products_from_neo4j():
    """
    Kết nối và truy vấn các node Product từ Neo4j.
    Mỗi sản phẩm được chuyển thành một chuỗi văn bản chứa thông tin từ các trường:
      Tên sản phẩm, Mã sản phẩm, Trạng thái, Giá gốc, Giảm giá, Giá bán, Link sản phẩm, 
      Link hình ảnh, Màu sắc, Size, Đặc điểm.
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    products = []
    with driver.session() as session:
        query = "MATCH (p:Product) RETURN p"
        result = session.run(query)
        for record in result:
            p = record["p"]
            product_text = (
                f"Tên sản phẩm: {p.get('name', '')}\n"
                f"Mã sản phẩm: {p.get('code', '')}\n"
                f"Trạng thái: {p.get('status', '')}\n"
                f"Giá gốc: {p.get('original_price', '')}\n"
                f"Giảm giá: {p.get('discount', '')}\n"
                f"Giá bán: {p.get('sale_price', '')}\n"
                f"Link sản phẩm: {p.get('product_link', '')}\n"
                f"Link hình ảnh: {p.get('image_link', '')}\n"
                f"Màu sắc: {p.get('color', '')}\n"
                f"Size: {p.get('size', '')}\n"
                f"Đặc điểm: {p.get('features', '')}\n"
            )
            products.append(product_text)
    driver.close()
    return products

async def initialize_rag():
    """
    Khởi tạo LightRAG với cấu hình sử dụng OpenAI GPT-4o-mini.
      - llm_model_func: Sử dụng gpt_4o_mini_complete (cho sinh text).
      - embedding_func: Sử dụng openai_embed để tạo vector embedding.
    """
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

async def main():
    logging.info("Khởi tạo LightRAG...")
    rag = await initialize_rag()
    logging.info("LightRAG đã sẵn sàng.")

    # Fetch dữ liệu sản phẩm từ Neo4j
    logging.info("Đang truy vấn dữ liệu từ Neo4j...")
    products = fetch_products_from_neo4j()
    logging.info(f"Đã lấy được {len(products)} sản phẩm từ Neo4j.")

    # Insert các văn bản từ sản phẩm vào hệ thống LightRAG
    for idx, product_text in enumerate(products, 1):
        logging.info(f"Insert sản phẩm {idx} vào hệ thống...")
        # Hàm insert của LightRAG là synchronous; không cần dùng await
        rag.insert(product_text)
    logging.info("Insert xong toàn bộ sản phẩm.")

    # Thực hiện truy vấn trên dữ liệu đã index
    query_text = "Tìm thông tin về sản phẩm Dep nam chữ H quai da thật"  # Thay đổi câu hỏi phù hợp với dữ liệu của bạn
    logging.info("Thực hiện truy vấn...")
    result = rag.query(query_text, param=QueryParam(mode="hybrid"))
    print("\nKết quả truy vấn:", result)

if __name__ == "__main__":
    asyncio.run(main())
