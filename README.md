# LogTagger

![LogTagger Logo](docs/images/logo.png) <!-- You would need to add this logo file -->

## 🔍 Overview

LogTagger is a specialized tool designed for automated and semi-automated labeling of cybersecurity logs to create high-quality datasets for training AI models, including Large Language Models (LLMs). It integrates with Security Information and Event Management (SIEM) systems, receives logs, performs automatic classification, applies standardized tags (e.g., MITRE ATT&CK), allows for expert manual refinement, and exports the processed data for AI model training.

## 🌟 Key Features

- **SIEM Integration**: Connect with Wazuh, Splunk, Elastic, and other SIEM systems via REST API
- **Automatic Log Labeling**: Apply tags based on predefined rules (True_positive, False_positive, Attack_Type)
- **MITRE ATT&CK Framework**: Automatic identification of tactics and techniques
- **Semi-Automatic Labeling**: Support for expert review and manual tag adjustment
- **Advanced ML Classification**: 
  - Modular ML provider system supporting local, API and demo modes
  - Classification confidence metrics with configurable thresholds
  - Human verification workflow for ML-classified events
  - Performance metrics tracking and visualization
- **Dataset Export**: Generate structured CSV or JSON datasets for AI training
- **Visualization Dashboard**: Web interface for log review, manual tagging, and analytics

## 🔧 Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: React (JavaScript)
- **Database**: PostgreSQL
- **Containerization**: Docker
- **Authentication**: JWT-based authentication system
- **Machine Learning**:
  - Local ML with scikit-learn
  - Remote ML API integration
  - Performance metrics tracking

## ⚙️ Installation

### Prerequisites

- Python 3.8+ 
- Node.js 14+
- PostgreSQL 12+
- Git

### Quick Setup (Automated)

The easiest way to get started is by using our automated setup script:

```bash
# Clone the repository
git clone https://github.com/yourusername/logtagger.git
cd logtagger

# Run the setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Install all required dependencies
- Set up the PostgreSQL database
- Configure the application
- Create a default admin user (username: `admin`, password: `admin`)

### Manual Setup

If you prefer to set up manually:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/logtagger.git
   cd logtagger
   ```

2. **Set up the backend**:
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up the database**:
   ```bash
   # Create PostgreSQL database
   createuser -P logtagger  # Use 'logtagger' as the password when prompted
   createdb -O logtagger logtagger
   
   # Update config if needed
   # Edit backend/config.py with your database details
   ```

4. **Set up the frontend**:
   ```bash
   cd ../frontend
   npm install
   ```

## 🚀 Running the Application

### Using the Start Script

After installation, you can start both backend and frontend with:

```bash
./start.sh
```

### Manual Start

1. **Start the backend server**:
   ```bash
   cd backend
   source ../venv/bin/activate  # On Windows: ..\venv\Scripts\activate
   python app.py
   ```
   The backend API will be available at http://localhost:5000

2. **Start the frontend development server**:
   ```bash
   cd frontend
   npm start
   ```
   The frontend will be available at http://localhost:3000

3. **Login with default credentials**:
   - Username: `admin`
   - Password: `admin`
   
   **Important**: Change the default password immediately after first login.

## 📊 Database Structure

LogTagger uses a PostgreSQL database with two main tables:
- `events` - Structured security events with labeling information
- `raw_logs` - Raw log data from SIEM systems
- `ml_performance_metrics` - Metrics tracking ML model performance

To inspect your database structure:
```bash
cd backend
python tools/inspect_database.py
```

## 🤖 Machine Learning Integration

LogTagger features a flexible ML subsystem with the following capabilities:

1. **Modular ML Provider System**:
   - **Local ML**: Use scikit-learn based models for offline classification
   - **API ML**: Connect to external ML service via REST API
   - **Demo Provider**: Run with simulated ML for testing and demonstrations

2. **ML Dashboard**:
   - Monitor model performance with precision, recall, and F1 metrics
   - Track performance by attack type classification
   - Review ML-classified events and provide human verification

3. **Configuration Options**:
   - Set confidence thresholds for auto-applying labels
   - Configure human verification requirements
   - Enable/disable ML classification system-wide

To use ML features:
1. Navigate to "System Configuration" and enable ML classification
2. Configure ML API endpoints or use the built-in local model
3. Access the ML Dashboard to monitor performance and verify events

## 🔒 Security

- All API requests use HTTPS with SSL/TLS
- Authentication is handled via JWT tokens
- Role-based authorization (Admin, Analyst, Viewer)
- Regular database backups are recommended

## 📄 Documentation

For more detailed documentation:
- [API Documentation](docs/api.md)
- [SIEM Integration Guide](docs/siem-integration.md)
- [ML Integration Guide](docs/ml-integration.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the [MIT License](LICENSE).
