import csv
from neo4j import GraphDatabase

# Cấu hình kết nối Neo4j và file CSV
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "12345678"
CSV_FILE = "sanpham.csv"

def insert_product(tx, item):
    # Lấy dữ liệu từng trường và loại bỏ khoảng trắng
    category = item['Danh mục'].strip()
    subcategory = item['Danh mục con'].strip()
    product_name = item['Tên sản phẩm'].strip()
    product_code = item['Mã sản phẩm'].strip()
    color = item['Màu sắc'].strip()
    size = item['Size'].strip()  # Nếu cần phân tách thành list: size.split(",")
    status = item['Tình trạng'].strip()
    try:
        original_price = float(item['Giá gốc']) if item['Giá gốc'] else None
    except Exception as e:
        original_price = None
    discount = item['Giảm giá'].strip() if item['Giảm giá'] else None
    try:
        sale_price = float(item['Giá bán']) if item['Giá bán'] else None
    except Exception as e:
        sale_price = None
    product_link = item['Link sản phẩm'].strip()
    image_link = item['Link hình ảnh'].strip()
    features = item['Đặc điểm'].strip()

    # Sử dụng MERGE để tạo các node và quan hệ
    tx.run(
        """
        MERGE (c:Category {name: $category})
        MERGE (sc:Subcategory {name: $subcategory})
        MERGE (p:Product {code: $product_code})
          ON CREATE SET p.name = $product_name,
                        p.status = $status,
                        p.original_price = $original_price,
                        p.discount = $discount,
                        p.sale_price = $sale_price,
                        p.product_link = $product_link,
                        p.image_link = $image_link,
                        p.color = $color,
                        p.size = $size,
                        p.features = $features
        MERGE (p)-[:BELONGS_TO]->(sc)
        MERGE (sc)-[:PART_OF]->(c)
        """,
        category=category,
        subcategory=subcategory,
        product_name=product_name,
        product_code=product_code,
        status=status,
        original_price=original_price,
        discount=discount,
        sale_price=sale_price,
        product_link=product_link,
        image_link=image_link,
        color=color,
        size=size,
        features=features
    )

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                session.write_transaction(insert_product, row)
                count += 1
                print(f"Inserted {count} products", end="\r")
    driver.close()
    print("\n✅ Completed importing CSV into Neo4j.")

if __name__ == '__main__':
    main()
