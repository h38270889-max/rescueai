import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file if available
load_dotenv()

env_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(env_name)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f" ResQAI: Emergency Triage and Disaster Support System")
    print(f" Server running at: http://127.0.0.1:{port}")
    print(f" Environment: {env_name.title()}")
    print(f"=======================================================\n")
    app.run(host='127.0.0.1', port=port, debug=(env_name == 'development'))
