# Conference Data Extraction & Dashboard

## Setup & Execution Steps

### Clone the repository
```
git clone https://github.com/taha20181/data-scraper.git
```

### Create and activate a virtual environment
* On macOS/Linux:
```
python -m venv venv
source venv/bin/activate
```
* On Windows:
```
python -m venv venv
venv\Scripts\activate
```

### Install dependencies
```
pip install -r requirements.txt
```

### Run database migrations
```
python manage.py migrate
```
### Run the scraper management command
```
python manage.py scrape_data
```

#### Scrape a particular type
```
python manage.py scrape_data --type sessions/posters/all (default all)
```

### Run Django Server
```
python manage.py runserver
```
###### Access the UI at http://127.0.0.1:8000
