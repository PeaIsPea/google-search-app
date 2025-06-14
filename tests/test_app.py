import unittest
import json
from unittest.mock import patch
from app import app # Import Flask app của bạn

class GoogleSearchAppTests(unittest.TestCase):

    def setUp(self):
        """
        Thiết lập môi trường test trước mỗi bài test.
        """
        app.config['TESTING'] = True # Bật chế độ testing cho Flask
        self.app = app.test_client() # Tạo một test client để gửi request tới app

    def test_home_page(self):
        """
        Kiểm tra trang chủ (/) trả về HTTP 200 OK.
        """
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Google Search Scraper', response.data) # Kiểm tra nội dung trang

    @patch('app.GoogleSearch') # Mock GoogleSearch để không gọi API thật
    def test_search_api_success(self, MockGoogleSearch):
        """
        Kiểm tra API /search trả về kết quả thành công.
        Mock SerpAPI để trả về dữ liệu giả định.
        """
        # Thiết lập mock object để bắt chước hành vi của GoogleSearch
        mock_instance = MockGoogleSearch.return_value
        mock_instance.get_dict.return_value = {
            'organic_results': [
                {'title': 'Test Title 1', 'link': 'http://example1.com'},
                {'title': 'Test Title 2', 'link': 'http://example2.com'}
            ]
        }

        # Gửi request đến API /search
        response = self.app.get('/search?q=test_keyword')
        self.assertEqual(response.status_code, 200) # Kiểm tra status code
        data = json.loads(response.data) # Parse JSON response

        # Kiểm tra dữ liệu trả về
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['title'], 'Test Title 1')
        self.assertEqual(data[0]['url'], 'http://example1.com')
        self.assertEqual(data[1]['title'], 'Test Title 2')
        self.assertEqual(data[1]['url'], 'http://example2.com')

        # Đảm bảo SerpAPI đã được gọi đúng tham số
        MockGoogleSearch.assert_called_once_with({
            "q": "test_keyword",
            "api_key": app.config['SERPAPI_API_KEY'], # SERPAPI_API_KEY từ app.py
            "hl": "en",
            "gl": "us",
            "num": 10
        })
        mock_instance.get_dict.assert_called_once() # Đảm bảo get_dict được gọi

    @patch('app.GoogleSearch')
    def test_search_api_no_results(self, MockGoogleSearch):
        """
        Kiểm tra API /search khi không có kết quả từ SerpAPI.
        """
        mock_instance = MockGoogleSearch.return_value
        mock_instance.get_dict.return_value = {
            'organic_results': [] # Không có kết quả
        }

        response = self.app.get('/search?q=no_results_keyword')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)

    @patch('app.GoogleSearch')
    def test_search_api_serpapi_error(self, MockGoogleSearch):
        """
        Kiểm tra API /search khi SerpAPI trả về lỗi.
        """
        mock_instance = MockGoogleSearch.return_value
        # Giả lập SerpAPI trả về lỗi
        mock_instance.get_dict.return_value = {
            'error': 'API Key is invalid'
        }

        response = self.app.get('/search?q=error_keyword')
        self.assertEqual(response.status_code, 500) # Mong đợi lỗi 500 từ Flask
        data = json.loads(response.data)
        self.assertIn("SerpAPI Error: API Key is invalid", data['error'])
        #self.assertIn("API Key is invalid", data['error'])


    @patch('app.GoogleSearch')
    def test_search_api_missing_query(self, MockGoogleSearch):
        """
        Kiểm tra API /search khi thiếu tham số 'q'.
        """
        response = self.app.get('/search') # Không có ?q=
        self.assertEqual(response.status_code, 400) # Mong đợi lỗi 400 Bad Request
        data = json.loads(response.data)
        self.assertIn("Keyword 'q' is required.", data['error'])
        MockGoogleSearch.assert_not_called() # Đảm bảo SerpAPI không được gọi

if __name__ == '__main__':
    unittest.main()