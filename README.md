# Bhagavad Gita Search Application

This is a Flask application that allows users to search for verses from the Bhagavad Gita and get detailed information and AI-generated summaries.

## Prerequisites

- Python 3.9 or higher
- Git
- Virtualenv

## Setup Instructions

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/nyd-hackathon.git
    cd nyd-hackathon
    ```

2. **Create a virtual environment**:

    ```bash
    python -m venv venv
    ```

3. **Activate the virtual environment**:

    - On Windows:
        ```bash
        venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4. **Install the required dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

5. **Set up environment variables**:

    Create a `.env` file in the root directory of the project and add the following environment variables:

    ```env
    DATABASE_URL=your_database_url
    MISTRAL_API_KEY=your_mistral_api_key
    MODEL=mistral-small-2402
    ```

6. **Run the application**:

    ```bash
    python app.py
    ```

7. **Access the application**:

    Open your web browser and go to `http://localhost:5000` to use the website.

## Video Demonstration
https://github.com/user-attachments/assets/4c6281c7-c3ff-4f68-8396-889b75d007ab



## License

This project is licensed under the MIT License.
