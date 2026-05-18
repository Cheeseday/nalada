from app import create_app
from config import Config
from db.database import check_connection

app = create_app()

if __name__ == "__main__":
    Config.validate()
    check_connection()
    app.run(debug=Config.DEBUG)