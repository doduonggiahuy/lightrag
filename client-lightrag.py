import streamlit as st
import requests
import re

st.title("Chatbot Bán Giày")

st.markdown("Nhập câu hỏi của bạn để tìm thông tin sản phẩm:")

user_query = st.text_input("Câu hỏi:")

if st.button("Gửi câu hỏi"):
    if user_query:
        try:
            # Gọi API server tại địa chỉ (đảm bảo API server đang chạy)
            response = requests.get("http://localhost:8000/query", params={"q": user_query})
            if response.status_code == 200:
                data = response.json()
                result_markdown = data.get("result", "")
                
                # Ẩn phần References (nếu có) bằng cách tách chuỗi trước "### References"
                result_without_references = re.split(r"### References", result_markdown)[0]
                
                # Tìm URL hình ảnh sản phẩm, định dạng: ![Hình ảnh sản phẩm](URL)
                image_match = re.search(r"!\[Hình ảnh sản phẩm\]\((.*?)\)", result_without_references)
                if image_match:
                    image_url = image_match.group(1)
                    # Loại bỏ dòng markdown ảnh khỏi kết quả để tránh trùng lặp khi hiển thị
                    result_without_references = re.sub(r"!\[Hình ảnh sản phẩm\]\(.*?\)", "", result_without_references)
                    st.image(image_url, caption="Hình ảnh sản phẩm", use_column_width=True)
                    
                st.markdown("### Kết quả truy vấn:")
                st.markdown(result_without_references)
            else:
                st.error(f"Lỗi API: {response.status_code}")
        except Exception as e:
            st.error(f"Lỗi khi gọi API: {e}")
    else:
        st.warning("Vui lòng nhập câu hỏi.")

st.markdown("---")
