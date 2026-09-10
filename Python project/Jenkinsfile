pipeline {
    agent any

    environment {
        APP_DIR       = "/opt/kidney-disease-streamlit"
        VENV_DIR      = "${APP_DIR}/venv"
        APP_PORT      = "8501"
    }

    stages {

        stage('Checkout') {
            steps {
                echo '📥 Checking out source code...'
                checkout scm
            }
        }

        stage('Show Changes') {
            steps {
                echo '🔍 Comparing with previous build...'
                sh '''
                    chmod +x show_changes.sh
                    ./show_changes.sh
                '''
            }
        }

        stage('Prepare App Directory') {
            steps {
                echo '📁 Preparing deployment directory...'
                sh '''
                    mkdir -p ${APP_DIR}
                    cp -r ./* ${APP_DIR}/
                '''
            }
        }

        stage('Python Setup') {
            steps {
                echo '🐍 Setting up Python environment...'
                sh '''
                    cd ${APP_DIR}
                    python3 --version
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Running basic checks...'
                sh '''
                    cd ${APP_DIR}
                    . venv/bin/activate
                    python -m py_compile app.py
                    echo "Python syntax check passed!"
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo '🚀 Restarting Streamlit via systemd...'
                sh '''
                    sudo systemctl restart kidney-streamlit
                    sleep 5
                    sudo systemctl is-active kidney-streamlit
                '''
            }
        }

        stage('Health Check') {
            steps {
                echo '❤️ Checking Streamlit application...'
                sh '''
                    sleep 5
                    curl -f http://localhost:${APP_PORT}/_stcore/health
                    echo ""
                    echo "✅ Streamlit application is running!"
                '''
            }
        }
    }

    post {
        success {
            echo 'PIPELINE SUCCESSFUL - App running at http://<server-ip>:8501'
        }
        failure {
            echo 'PIPELINE FAILED — check console output'
            sh 'sudo journalctl -u kidney-streamlit -n 50 --no-pager || true'
        }
    }
}