import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS # Dùng để cho phép frontend gọi backend từ domain khác

from serpapi import GoogleSearch
import re # Dùng để xử lý regex cho việc trích xuất URL

app = Flask(__name__,
            template_folder='templates',
            static_folder='static') # Khai báo thư mục templates và static
CORS(app) # Enable CORS for all routes

app.config['SERPAPI_API_KEY'] = os.environ.get("SERPAPI_API_KEY", "36a315fbc807a9ca97354a0f39e1c5cc3e3fd9bfeba99270442c5dfeb25e4690") # <-- Đặt API Key của bạn vào đây





_cached_search_results = []

@app.route('/')
def home():
    """
    Route để phục vụ file index.html (trang chủ của ứng dụng).
    """
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search_google():
    """
    API endpoint để thực hiện tìm kiếm trên Google (qua SerpAPI) và trả về kết quả JSON.
    """
    global _cached_search_results # Khai báo sử dụng biến toàn cục

    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Keyword 'q' is required."}), 400

    try:
        # Cấu hình tham số cho yêu cầu tìm kiếm SerpAPI
        params = {
            "q": query,         # Từ khóa tìm kiếm
            "api_key": app.config['SERPAPI_API_KEY'], # API Key
            "hl": "en",         # Ngôn ngữ kết quả (ví dụ: tiếng Anh)
            "gl": "us",         # Quốc gia tìm kiếm (ví dụ: Hoa Kỳ)
            "num": 10           # Số lượng kết quả organic_results muốn lấy (tối đa 100)
            
        }

        # Khởi tạo đối tượng GoogleSearch và thực hiện tìm kiếm
        search = GoogleSearch(params)
        results_data = search.get_dict() # Lấy kết quả dưới dạng dictionary

        # Xử lý và trích xuất các kết quả tìm kiếm tự nhiên (organic_results)
        results = []
        if 'organic_results' in results_data:
            for item in results_data['organic_results']:
                title = item.get('title')
                link = item.get('link')

                if title and link:
                    results.append({
                        "title": title,
                        "url": link
                    })
        else:
            # Nếu không có organic_results, có thể có lỗi hoặc không có kết quả
            print(f"SerpAPI did not return 'organic_results'. Full response: {results_data.keys()}")
            # Bạn có thể kiểm tra 'error' field nếu có
            if 'error' in results_data:
                print(f"SerpAPI Error: {results_data['error']}")
                return jsonify({"error": f"SerpAPI Error: {results_data['error']}"}), 500

        _cached_search_results = results # Cache results for download
        return jsonify(results)

    except Exception as e:
        print(f"An error occurred with SerpAPI search: {e}")
        return jsonify({"error": f"An error occurred during search: {e}"}), 500

if __name__ == '__main__':
    # Khi chạy cục bộ, Flask sẽ chạy trên cổng 5000
    # Khi deploy lên Render/Railway, họ sẽ cung cấp PORT qua biến môi trường
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port) # host='0.0.0.0' để cho phép truy cập từ bên ngoài nếu cần