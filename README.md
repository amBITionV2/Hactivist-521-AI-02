# Cognitive Crime Analysis System

The Cognitive Crime Analysis System is a full-stack, multimodal AI application designed to assist detectives and analysts in modern criminal investigations. By leveraging cutting-edge AI models, it transforms unstructured case files (both text and images) into a structured, interactive knowledge graph and generates actionable intelligence.

This project demonstrates a complete end-to-end workflow, from data ingestion and background processing to advanced AI-driven analysis and a professional user interface.

## 🌟 Features

-   **Multimodal Data Ingestion**: Upload and process both text-based case files (`.txt`) and visual evidence (`.jpg`, `.png`, etc.).
-   **AI Knowledge Graph Generation**: Uses the Gemini LLM to automatically extract key entities (people, places, times) and, more importantly, the relationships between them from unstructured text.
-   **Interactive Graph Visualization**: Displays the complex web of relationships for each case in a clean, hierarchical, and interactive graph.
-   **AI Crime Simulation**: Generates a plausible, step-by-step narrative of how a crime likely occurred based on the evidence in the knowledge graph.
-   **Conversational AI Detective**: A chat interface that allows users to ask questions about a case. The AI uses a Retrieval-Augmented Generation (RAG) approach to reason over the facts in the knowledge graph and provide insightful answers.
-   **AI Suspect Image Generation**: Generates a realistic police sketch of a suspect based on a textual description using the Imagen model.

## 📸 Screenshots

-   **Main Dashboard**: The main view for uploading files and seeing the list of all processed cases.
-   **Case Detail View**: The three-column dashboard showing the Knowledge Graph, the Inference Engine with the AI Detective and Suspect Generator, and the AI Analysis panel.

## 🛠️ Tech Stack & Architecture

This project is built with a modern, scalable architecture that separates concerns into distinct services.

| Category  | Technology                  | Description                                            |
| :-------- | :-------------------------- | :----------------------------------------------------- |
| Backend   | Python 3, FastAPI           | For building the robust, high-performance REST API.    |
| Frontend  | React (Vite), Tailwind CSS, Axios | For a modern, responsive, and beautifully styled UI.   |
| Databases | PostgreSQL, Neo4j           | PostgreSQL for structured metadata; Neo4j for graph data. |
| AI / ML   | Google Gemini & Imagen      | For text analysis, reasoning, and image generation.    |
| Workers   | Celery, Redis               | For managing and executing long-running background tasks. |
| UI Libs   | vis-network                 | For rendering the interactive knowledge graph.         |

## 🚀 Setup and Installation

To run this project locally, you will need to set up the backend and frontend separately.

### Prerequisites

-   Python 3.10+
-   Node.js and npm
-   PostgreSQL server
-   Neo4j Desktop
-   Docker Desktop (to run Redis)

### Backend Setup (`cognitive_crime_analysis`)

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd cognitive_crime_analysis
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    -   Create a file named `.env` in the root of the backend project.
    -   Add your Gemini API key:
        ```env
        GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```

5.  **Configure Passwords:**
    -   Open `app/database.py` and set your PostgreSQL password.
    -   Open `app/main.py`, `app/api/detective.py`, and `workers/tasks.py` and set your Neo4j password.

### Frontend Setup (`crime-analysis-ui`)

1.  **Navigate to the UI directory:**
    ```bash
    cd ../crime-analysis-ui
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

## ▶️ Running the Application

You will need to run four separate processes in four different terminals.

1.  **Start Redis (via Docker):**
    -   Navigate to the backend root (`cognitive_crime_analysis`).
    -   Run:
        ```bash
        docker-compose up -d
        ```

2.  **Start the Celery Worker:**
    -   Navigate to the backend root.
    -   Activate the virtual environment.
    -   Run:
        ```bash
        celery -A workers.tasks worker --loglevel=INFO --pool=solo
        ```

3.  **Start the FastAPI Server:**
    -   Navigate to the backend root.
    -   Activate the virtual environment.
    -   Run:
        ```bash
        uvicorn app.main:app --reload
        ```

4.  **Start the React App:**
    -   Navigate to the frontend root (`crime-analysis-ui`).
    -   Run:
        ```bash
        npm run dev
        ```

You can now access the web application at **http://localhost:5173**.

##  How to Use

1.  Use the "Upload New Case File" section to upload a `.txt` file with a crime report or an image file (`.jpg`, `.png`).
2.  The file will appear in the "Case Dashboard" with a "processing" status.
3.  Click "Refresh List" after a few moments. The status should change to "complete".
4.  Click on any completed case to open the detailed analysis view.
5.  Interact with the Knowledge Graph, ask questions to the AI Detective, and generate suspect images.
