Simple Server with throttling to manage products

the api endpoints are: 
basic CRUD (Create, Read, Update, Delete)  POST /product, GET /product/{id}, PUT /product/{id}, DELETE /product/{id}

Endpoint to increment a product view counter with race condition protection
POST /products/{product_id}/increment_views

Endpoint to trigger background processing
POST /process_data/{product_id}

Run the server
pip install -r requirements.txt
uvicorn server:app --reload
Redis must running on port 6379

Test race condition protection
python test_increment_views.py

Test all endpoints
pytest test_all_endpoints.py -s






