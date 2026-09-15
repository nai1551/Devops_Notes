pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'npm ci'
            }
        }

        stage('Test') {
            steps {
                sh 'npm test'
            }
        }
    }

    post {
        success {
            echo 'Tests passed.'
        }
        failure {
            echo 'Pipeline failed - check the stage logs above.'
        }
        always {
            // Clean up the SQLite file created during tests so builds stay reproducible
            sh 'rm -f todos.db'
        }
    }
}
