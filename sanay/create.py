from flask import Flask
from models import *

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://joeqoeubnocowo:7ae138822b0a6611ce524674312e724400bff93bf8566f789a9ccc21c5802240@ec2-54-161-239-198.compute-1.amazonaws.com:5432/d6711g835q321m' #os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db.init_app(app)

def main():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        main()
